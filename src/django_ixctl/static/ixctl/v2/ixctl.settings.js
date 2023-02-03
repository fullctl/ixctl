(function($, $tc, $ctl) {
$ctl.application.Ixctl.Settings = $tc.extend(
  "Settings",
  {
    Settings : function() {
      this.urlparam = "edit-rs"
      this.Tool("nets");
    },

    format_request_url : function(url) {
      return url.replace("ix_tag", fullctl.ixctl.ix_object().slug);
    },

    menu : function() {
      var menu = this.Tool_menu();

      this.widget("routeservers", ($e) => {
        return new twentyc.rest.List(
          this.template("routeservers", this.$e.menu.find('.routeservers'))
        );
      })

      this.$w.routeservers.formatters.row = (row, data) => {
        row.click(() =>{
          this.edit_routeserver(data);
        });
      };

      this.$w.routeservers.format_request_url = (url) => {
        return url.replace("ix_tag", fullctl.ixctl.ix_object().slug);
      };

      menu.find('[data-element="button_add_routeserver"]').click(()=>{
        this.create_routeserver();
      });

      menu.find('[data-element="button_delete_ix"]').click(()=>{
        this.delete_exchange();
      });

      menu.find('[data-element="button_general_settings"]').click(()=>{
        this.general_settings();
      });


      return menu;
    },

    sync : function() {
      var exchange = $ctl.ixctl.ix_object();
      this.$w.routeservers.load();
      if(exchange) {
        this.$e.menu.find('[data-element="button_add_routeserver"]').grainy_toggle(exchange.grainy, "c");
        this.$e.menu.find('[data-element="button_delete_ix"]').grainy_toggle(exchange.grainy, "d");
        this.$e.menu.find('[data-element="button_general_settings"]').grainy_toggle(exchange.grainy, "u");
      } else {
        this.$e.menu.find('[data-element="button_delete_exchange"]').hide();
        this.$e.menu.find('[data-element="button_general_settings"]').hide();
        this.$e.menu.find('[data-element="button_add_routeserver"]').hide();
      }
    },

    unload_dialog : function() {
      this.$e.body.empty();
    },

    general_settings : function() {
      var ix = $ctl.ixctl.ix_object();
      var dialog = this.custom_dialog("General settings for "+ix.name);
      var form = new twentyc.rest.Form(
        this.template("form_general_settings", dialog)
      );
      form.format_request_url = this.format_request_url;
      form.fill(ix);

      $(form).on("api-write:success", ()=>{
        $ctl.ixctl.refresh().then(()=>{
          $ctl.ixctl.select_ix(ix.id);
        });
      });
    },


    delete_exchange : function() {
      var ix = $ctl.ixctl.ix_object();
      var dialog = this.custom_dialog("Delete "+ix.name);

      var form = this.template("form_delete_ix", dialog);
      var button = new twentyc.rest.Button(
        form.find('[data-element="button_delete_ix_proceed"]')
      );

      button.action = ix.slug;
      $(button).on("api-write:success", () => {
        $ctl.ixctl.refresh().then(() => {
          $ctl.ixctl.unload_ix(ix.id);
          $ctl.ixctl.select_ix();
          $ctl.ixctl.page("overview");
        });
      });

      form.find('.ix-name').text(ix.name);
    },

    create_routeserver : function() {

      var dialog = this.custom_dialog('Create route server');

      var rs_wiz = new $ctl.widget.Wizard(this.template("routeserver_wizard", dialog));
      var rs_pdb_list = new twentyc.rest.List(
        this.template("routeserver_pdb_list", rs_wiz.element.find('.pdbrouteserver-list'))
      );
      var form = new twentyc.rest.Form(
        this.template("form_routeserver_page", rs_wiz.element.find('.rs-form'))
      );
      var button_delete = form.element.find('[data-element="rs_delete"]');

      var form_defaults = {
        rpki_bgp_origin_validation: true,
        graceful_shutdown: true
      };

      rs_pdb_list.format_request_url = this.format_request_url;

      rs_pdb_list.formatters.row = (row, data) => {
        row.find('button').click(() =>{
          form.fill(data);
          rs_wiz.set_step(2);
        });
      };

      $(rs_pdb_list).on("load:after", () => {
        if(!rs_pdb_list.list_body.find('tr.rs-row').length) {
          rs_wiz.set_step(2);
          button_delete.hide();
        }
      });

      rs_pdb_list.load();

      form.format_request_url = this.format_request_url;
      form.reset();
      form.fill(form_defaults);

      button_delete.find('span.label').text('Back');
      button_delete.click(() => { rs_wiz.set_step(1); form.reset(); form.fill(form_defaults) });


      $(form).on("api-write:success", (ev, e, payload) => {
        fullctl.ixctl.$t.routeservers.sync();
        fullctl.ixctl.page('overview');
        this.unload_dialog();
      });

    },


    edit_routeserver : function(rs) {
      console.log("editing", rs);

      var form = new twentyc.rest.Form(
        this.template("form_routeserver_page", this.custom_dialog('Edit '+rs.name))
      );
      var button_delete = new twentyc.rest.Button(
        form.element.find('[data-element="rs_delete"]')
      );
      button_delete.format_request_url = this.format_request_url
      button_delete.action = rs.id;

      form.form_action = rs.id;
      form.method = "put";
      form.format_request_url = this.format_request_url;


      $(form).on("api-write:before", (ev, e, payload) => {
        payload["ix"] = rs.ix;
        payload["id"] = rs.id;
      });


      $(form).on("api-write:success", (ev, e, payload) => {
        fullctl.ixctl.$t.routeservers.sync();
        fullctl.ixctl.page('overview');
      });

      $(button_delete).on("api-write:success", (ev, e, payload) => {
        fullctl.ixctl.$t.routeservers.sync();
        fullctl.ixctl.page('overview');
        this.unload_dialog();
      });


      form.fill(rs);

    }

  },
  $ctl.application.Tool
);


$($ctl).on("init_tools", (e, app) => {
  app.tool("settings", () => {
    return new $ctl.application.Ixctl.Settings();
  })

  $('#settings-tab').on('show.bs.tab', () => {
    app.$t.settings.sync();
    app.$t.settings.general_settings();
  });
});



})(jQuery, twentyc.cls, fullctl);
