(function($, $tc, $ctl) {

$ctl.application.Ixctl = $tc.extend(
  "Ixctl",
  {
    Ixctl : function() {
      this.Application("ixctl");

      this.urlkeys = {}

      this.$c.header.app_slug = "ix";
      this.$c.toolbar.widget("select_ix", ($e) => {
        var w = new twentyc.rest.Select($e.select_ix);
        $(w).on("load:after", (event, element, data) => {
          var i;
          for(i = 0; i < data.length; i++)
            this.urlkeys[data[i].id] = data[i].urlkey;
          if(data.length == 0)
            this.prompt_import(true);
        });
        return w

      });

      console.log(this.$c.toolbar)
      $(this.$c.toolbar.$w.select_ix).one("load:after", () => {
        this.sync();
      });

      this.tool("members", () => {
        return new $ctl.application.Ixctl.Members();
      });

      $(this.$c.toolbar.$e.select_ix).on("change", () => {
        this.sync();
      });

      $(this.$c.toolbar.$e.button_import).click(() => {
        this.prompt_import();
      });

      $(this.$c.toolbar.$e.button_create_ix).click(() => {
        this.prompt_create_exchange();
      });

      this.$t.members.activate();

    },

    ix : function() {
      return this.$c.toolbar.$w.select_ix.element.val();
    },

    urlkey : function() {
      return this.urlkeys[this.ix()];
    },

    select_ix : function(id) {
      this.$c.toolbar.$e.select_ix.val(id);
      this.sync();
    },

    refresh : function() {
      return this.refresh_select_ix();
    },

    refresh_select_ix : function() {
      return this.$c.toolbar.$w.select_ix.refresh();
    },

    prompt_import : function(first_import) {
      return new $ctl.application.Ixctl.ModalImport(first_import);
    },

    prompt_add_member : function() {
      return new $ctl.application.Ixctl.AddMemberImport(this.ix());
    },

    prompt_create_exchange : function() {
      return new $ctl.application.Ixctl.ModalCreateIX();
    }

  },
  $ctl.application.Application
);

$ctl.application.Ixctl.ModalImport = $tc.extend(
  "ModalImport",
  {
    ModalImport : function(first_import) {
      var form = this.form = new twentyc.rest.Form(
        $ctl.template("form_import")
      );

      var modal = this;

      if(first_import)
        form.element.find('.first-import').show();

      $(this.form).on("api-write:success", function(event, endpoint, payload, response) {
        $ctl.ixctl.refresh().then(
          () => { $ctl.ixctl.select_ix(response.content.data[0].id) }
        );
        modal.hide();
      });
      this.Modal("continue", "Import from PeeringDB", form.element);
      // remove dupe
      form.element.find("span.select2").last().detach()
      form.wire_submit(this.$e.button_submit);
    }
  },
  $ctl.application.Modal
);




$ctl.application.Ixctl.ModalCreateIX = $tc.extend(
  "ModalCreateIX",
  {
    ModalCreateIX : function() {
      console.log($ctl.template("form_create_ix"));
      var form = this.form = new twentyc.rest.Form(
        $ctl.template("form_create_ix")
      );

      console.log(form);
      var modal = this;

      $(this.form).on("api-write:success", function(event, endpoint, payload, response) {
        console.log(response.content.data)
        $ctl.ixctl.refresh().then(
          () => { $ctl.ixctl.select_ix(response.content.data[0].id) }
        );
        modal.hide();
      });
      this.Modal("continue", "Create new exchange", form.element);
      // remove dupe
      // form.element.find("span.select2").last().detach()
      form.wire_submit(this.$e.button_submit);
    }
  },
  $ctl.application.Modal
);


$ctl.application.Ixctl.ModalMember = $tc.extend(
  "ModalMember",
  {
    ModalMember : function(ix_id, member) {
      var modal = this;
      var title = "Add Member"
      var form = this.form = new twentyc.rest.Form(
        $ctl.template("form_member")
      );

      this.member = member;

      form.base_url = form.base_url.replace("/0", "/"+ix_id);

      if(member) {
        title = "Edit "+member.display_name;
        form.form_action = "edit_member";
        form.method = "PUT"
        form.fill(member);
        $(this.form).on("api-write:before", (ev, e, payload) => {
          payload["ix"] = member.ix;
          payload["id"] = member.id;
        });
      }

      $(this.form).on("api-write:success", (ev, e, payload, response) => {
        $ctl.ixctl.$t.members.$w.list.load();
        modal.hide();
      });

      this.Modal("save", title, form.element);
      form.wire_submit(this.$e.button_submit);
    }
  },
  $ctl.application.Modal
);


$ctl.application.Ixctl.Members = $tc.extend(
  "Members",
  {
    Members : function() {
      this.Tool("members");
    },
    init : function() {
      this.widget("list", ($e) => {
        return new twentyc.rest.List(
          this.template("list", this.$e.body)
        );
      })

      this.$w.list.formatters.row = (row, data) => {
        row.find('a[data-action="edit_member"]').click(() => {
          var member = row.data("apiobject");
          new $ctl.application.Ixctl.ModalMember($ctl.ixctl.ix(), member);
        });
      };

      this.$w.list.formatters.speed = $ctl.formatters.pretty_speed;
      this.$w.list.base

      $(this.$w.list).on("api-read:before",function()  {
        console.log(this.base_url)
        this.base_url = this.base_url.replace(
          /\/ix\/\d+$/,
          "/ix/"+$ctl.ixctl.ix()
        )
      })
    },

    menu : function() {
      var menu = this.Tool_menu();
      menu.find('[data-element="button_add_member"]').click(() => {
        return new $ctl.application.Ixctl.ModalMember($ctl.ixctl.ix());
      });
      return menu;
    },

    sync : function() {
      if($ctl.ixctl.ix()) {
        this.$w.list.load();
        this.$e.menu.find('[data-element="button_ixf_export"]').attr(
          "href", this.jquery.data("ixf-export-url").replace("URLKEY", $ctl.ixctl.urlkey())
        )

        this.$e.menu.find('[data-element="button_api_view"]').attr(
          "href", this.$w.list.base_url + "/" + this.$w.list.action +"?pretty"
        )

      }
    }
  },
  $ctl.application.Tool
);

$(document).ready(function() {
  $ctl.ixctl = new $ctl.application.Ixctl();
});

})(jQuery, twentyc.cls, fullctl);
