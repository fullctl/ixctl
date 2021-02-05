(function($, $tc, $ctl) {

$ctl.application.Ixctl = $tc.extend(
  "Ixctl",
  {
    Ixctl : function() {
      this.Application("ixctl");

      this.urlkeys = {}
      this.exchanges = {}
      this.ix_slugs = {}
      this.initial_load = false

      this.$c.header.app_slug = "ix";
      this.$c.toolbar.widget("select_ix", ($e) => {
        var w = new twentyc.rest.Select($e.select_ix);
        $(w).on("load:after", (event, element, data) => {
          var i;
          for(i = 0; i < data.length; i++) {
            this.urlkeys[data[i].id] = data[i].urlkey;
            this.exchanges[data[i].id] = data[i];
            this.ix_slugs[data[i].id] = data[i].slug;
          }

          if(data.length == 0) {
            $e.select_ix.attr('disabled', true)
          } else {
            $e.select_ix.attr('disabled', false)
          }
        });
        return w

      });

      $(this.$c.toolbar.$w.select_ix).one("load:after", () => {
        params = new URLSearchParams(window.location.search)
        var preselect_ix = params.get("ix")
        if(preselect_ix) {
          this.select_ix(preselect_ix)
        } else {
          this.sync();
        }
      });

      this.tool("members", () => {
        return new $ctl.application.Ixctl.Members();
      });

      this.tool("routeservers", () => {
        return new $ctl.application.Ixctl.Routeservers();
      });


      $($ctl).trigger("init_tools", [this]);


      $(this.$c.toolbar.$e.select_ix).on("change", () => {
        this.sync();
      });

      $(this.$c.toolbar.$e.button_import).click(() => {
        this.prompt_import();
      });

      $(this.$c.toolbar.$e.button_create_ix).click(() => {
        this.prompt_create_exchange();
      });

      $(this.$c.toolbar.$e.button_update_ix).click(() => {
        this.prompt_update_exchange();
      });


      this.$t.members.activate();
      this.$t.routeservers.activate();

    },

    ix : function() {
      return this.$c.toolbar.$w.select_ix.element.val();
    },

    ix_slug : function() {
      return this.ix_slugs[this.ix()];
    },

    ix_object: function() {
      return this.exchanges[this.ix()]
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

    prompt_create_exchange : function() {
      return new $ctl.application.Ixctl.ModalCreateIX();
    },

    prompt_update_exchange : function() {
      return new $ctl.application.Ixctl.ModalUpdateIX();
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
      // console.log($ctl.template("form_create_ix"));
      var form = this.form = new twentyc.rest.Form(
        $ctl.template("form_create_ix")
      );

      // console.log(form);
      var modal = this;

      $(this.form).on("api-write:success", function(event, endpoint, payload, response) {
        // console.log(response.content.data)
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

$ctl.application.Ixctl.ModalUpdateIX = $tc.extend(
  "ModalUpdateIX",
  {
    ModalUpdateIX : function() {
      let ix = $ctl.ixctl.ix_object();

      var form = this.form = new twentyc.rest.Form(
        $ctl.template("form_update_ix")
      );
      form.base_url = form.base_url.replace("/default", "/"+ $ctl.ixctl.ix_slug());

      var modal = this;

      form.fill(ix)

      $(this.form).on("api-write:success", function(event, endpoint, payload, response) {
        $ctl.ixctl.refresh().then(
          () => { $ctl.ixctl.select_ix(response.content.data[0].id) }
        );
        modal.hide();
      });
      this.Modal("continue", "Edit exchange", form.element);
      form.wire_submit(this.$e.button_submit);
    }
  },
  $ctl.application.Modal
);


$ctl.application.Ixctl.ModalMember = $tc.extend(
  "ModalMember",
  {
    ModalMember : function(ix_slug, member) {
      var modal = this;
      var title = "Add Member"
      var form = this.form = new twentyc.rest.Form(
        $ctl.template("form_member")
      );

      this.member = member;
      form.base_url = form.base_url.replace("/default", "/"+ix_slug);

      if(member) {
        title = "Edit "+member.display_name;
        form.method = "PUT"
        form.form_action = member.id;
        form.fill(member);


        form.element.find('input[type="text"],select,input[type="checkbox"]').each(function() {
          if(!grainy.check(member.grainy+"."+$(this).attr("name"), "u")) {
            $(this).attr("disabled", true)
          }
        });


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
          new $ctl.application.Ixctl.ModalMember($ctl.ixctl.ix_slug(), member);
        }).each(function() {
          if(!grainy.check(data.grainy+".?", "u")) {
            $(this).hide()
          }
        });

        if(!grainy.check(data.grainy, "d")) {
          row.find('a[data-api-method="DELETE"]').hide();
        }
      };

      this.$w.list.formatters.speed = $ctl.formatters.pretty_speed;

      $(this.$w.list).on("api-read:before",function(endpoint)  {
        let url = this.base_url.split("/").slice(0,-1);
        url.push($ctl.ixctl.ix_slug());
        this.base_url = url.join("/");
      })

      this.initialize_sortable_headers("name");
    },

    menu : function() {
      var menu = this.Tool_menu();
      menu.find('[data-element="button_add_member"]').click(() => {
        return new $ctl.application.Ixctl.ModalMember($ctl.ixctl.ix_slug());
      });
      return menu;
    },

    sync : function() {
      var ix_id = $ctl.ixctl.ix()
      if(ix_id) {
        var exchange = $ctl.ixctl.exchanges[ix_id]
        console.log(exchange.grainy)
        if(grainy.check(exchange.grainy, "r")) {
          this.show();
          this.apply_ordering();
          this.$w.list.load();
          let ixf_export_url = this.jquery.data("ixf-export-url").replace("default", $ctl.ixctl.ix_slug());
          if ($ctl.ixctl.ix_object().ixf_export_privacy == "private"){
            ixf_export_url = ixf_export_url + "?secret=" + $ctl.ixctl.urlkey()
          }
          this.$e.menu.find('[data-element="button_ixf_export"]').attr(
            "href", ixf_export_url
          )

          this.$e.menu.find('[data-element="button_api_view"]').attr(
            "href", this.$w.list.base_url + "/" + this.$w.list.action +"?pretty"
          )

          if(grainy.check(exchange.grainy, "c")) {
            this.$e.menu.find('[data-element="button_add_member"]').show();
            this.$e.menu.find('[data-element="button_ixf_export"]').show();
          } else {
            this.$e.menu.find('[data-element="button_add_member"]').hide();
            this.$e.menu.find('[data-element="button_ixf_export"]').hide();
          }

        } else {
          this.hide();
        }
      } else {
        // no exchange exists - hide members tool
        this.hide();
      }
    },
  },
  $ctl.application.Tool
);

$ctl.application.Ixctl.ModalRouteserver = $tc.extend(
  "ModalRouteserver",
  {
    ModalRouteserver : function(ix_slug, routeserver) {
      var modal = this;
      var title = "Add Routeserver"
      var form = this.form = new twentyc.rest.Form(
        $ctl.template("form_routeserver")
      );

      this.routeserver = routeserver;

      form.base_url = form.base_url.replace("/default", "/"+ix_slug);

      if(routeserver) {
        title = "Edit "+routeserver.display_name;
        form.method = "PUT"
        form.form_action = routeserver.id;
        form.fill(routeserver);
        $(this.form).on("api-write:before", (ev, e, payload) => {
          payload["ix"] = routeserver.ix;
          payload["id"] = routeserver.id;
        });
      }

      $(this.form).on("api-write:success", (ev, e, payload, response) => {
        $ctl.ixctl.$t.routeservers.$w.list.load();
        modal.hide();
      });

      this.Modal("save_lg", title, form.element);
      form.wire_submit(this.$e.button_submit);
    }
  },
  $ctl.application.Modal
);


$ctl.application.Ixctl.Routeservers = $tc.extend(
  "Routeservers",
  {
    Routeservers : function() {
      this.Tool("routeservers");
    },
    init : function() {
      this.widget("list", ($e) => {
        return new twentyc.rest.List(
          this.template("list", this.$e.body)
        );
      })

      this.$w.list.formatters.row = (row, data) => {
        row.find('a[data-action="edit_routeserver"]').click(() => {
          var routeserver = row.data("apiobject");
          new $ctl.application.Ixctl.ModalRouteserver($ctl.ixctl.ix_slug(), routeserver);
        });

        row.find('a[data-action="view_rsconf"]').mousedown(function() {
          var routeserver = row.data("apiobject");
          let rsconfurl = row.data("rsconfurl");
          rsconfurl = rsconfurl.replace("default", $ctl.ixctl.ix_slug());
          rsconfurl = rsconfurl.replace("__replace__me__", routeserver.name);
          $(this).attr("href", rsconfurl)
        });
      };

      this.$w.list.formatters.speed = $ctl.formatters.pretty_speed;
      this.$w.list.base

      $(this.$w.list).on("api-read:before",function()  {
        let url = this.base_url.split("/").slice(0,-1);
        url.push($ctl.ixctl.ix_slug());
        this.base_url = url.join("/");
      })
    },

    menu : function() {
      var menu = this.Tool_menu();
      menu.find('[data-element="button_add_routeserver"]').click(() => {
        return new $ctl.application.Ixctl.ModalRouteserver($ctl.ixctl.ix_slug());
      });
      return menu;
    },

    sync : function() {
      var ix_id = $ctl.ixctl.ix()
      if(ix_id) {
        var exchange = $ctl.ixctl.exchanges[ix_id]
        var rs_namespace =exchange.grainy.replace(/^ix\./, "rs.")+".?"
        if(grainy.check(rs_namespace, "r")) {
          this.show();
          this.$w.list.load();
          this.$e.menu.find('[data-element="button_api_view"]').attr(
            "href", this.$w.list.base_url + "/" + this.$w.list.action +"?pretty"
          )
        } else {
          this.hide();
        }

      } else {
        // no exchanges exist - hide route-servers tool
        this.hide();
      }
    }
  },
  $ctl.application.Tool
);


$(document).ready(function() {
  $ctl.ixctl = new $ctl.application.Ixctl();
});

})(jQuery, twentyc.cls, fullctl);
