(function($, $tc, $ctl) {
$ctl.application.Ixctl.Settings = $tc.extend(
  "Settings",
  {
    Settings : function() {
      this.urlparam = "edit-rs"
      this.Tool("nets");
      this.activate();
    },

    format_request_url : function(url) {
      return url.replace("ix_tag", fullctl.ixctl.ix_object().slug);
    },

    menu : function() {
      var menu = this.Tool_menu();

      menu.find('[data-element="button_delete_ix"]').click(()=>{
        this.delete_exchange();
      });

      menu.find('[data-element="button_general_settings"]').click(()=>{
        this.general_settings();
      });


      return menu;
    },

    sync : function() {
      const exchange = $ctl.ixctl.ix_object();
      if(exchange) {
        this.$e.menu.find('[data-element="button_delete_ix"]').grainy_toggle(exchange.grainy, "d");
        this.$e.menu.find('[data-element="button_general_settings"]').grainy_toggle(exchange.grainy, "u");
      } else {
        this.$e.menu.find('[data-element="button_delete_exchange"]').hide();
        this.$e.menu.find('[data-element="button_general_settings"]').hide();
      }
      this.general_settings();
    },

    unload_dialog : function() {
      this.$e.body.empty();
    },

    general_settings : function() {
      var ix = $ctl.ixctl.ix_object();
      var dialog = this.custom_dialog("General settings for "+ix.name);
      const form = this.widget("form_general_settings", ($e) => {
        return new twentyc.rest.Form(
          this.template("form_general_settings", dialog)
        );
      })
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
  },
  $ctl.application.Tool
);


$($ctl).on("init_tools", (e, app) => {
  app.tool("settings", () => {
    return new $ctl.application.Ixctl.Settings();
  });

  $('#settings-tab').on('show.bs.tab', () => {
    app.$t.settings.sync();
  });

  if (window.location.hash == "#settings") {
    app.$t.settings.sync();
  }
});



})(jQuery, twentyc.cls, fullctl);
