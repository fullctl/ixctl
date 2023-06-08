(function($, $tc, $ctl) {

$ctl.application.Ixctl.Routeservers = $tc.extend(
  "Routeservers",
  {
    Routeservers : function() {
      this.Tool("routeservers");
      this.activate();
      this.view_list();
    },

    view_list : function() {
      // hide back to list button
      $(this.$e.menu).find('[data-element="button_list_view"]').hide()

      this.widget("list", ($e) => {
        return new twentyc.rest.List(
          this.template("list",
            this.custom_dialog('')
          )
        );
      })

      this.$w.list.formatters.row = (row, data) => {
        row.find('a[data-action="edit_routeserver"]').click(() => {
          const routeserver = row.data("apiobject");
          this.edit_routeserver(routeserver);
        }).grainy_toggle(data.grainy+".?", "u");

        if(!grainy.check(data.grainy, "d")) {
          row.find('a[data-api-method="DELETE"]').hide();
        }

        // wire "view config" button

        row.find('a[data-action="view_routeserver_config"]').mousedown(function() {
          var routeserver = row.data("apiobject");
          let routeserver_config_url = row.data("routeserver_config_url");
          routeserver_config_url = routeserver_config_url.replace("__ix_slug__", $ctl.ixctl.ix_slug());
          routeserver_config_url = routeserver_config_url.replace("__rs_name__", routeserver.name);
          $(this).attr("href", routeserver_config_url)
        });

        // wire "generate" config button

        var button_generate = new twentyc.rest.Button(row.find("[data-element=button_generate]"));

        // format button request url with the correct routeserver name

        button_generate.format_request_url = (url) => {
          var routeserver = row.data("apiobject");
          url = url.replace("__ix_slug__", $ctl.ixctl.ix_slug());
          return url.replace("__rs_name__", routeserver.name);
        };

        // on successful request to generate the status badge needs to
        // start polling for the status of the config generation

        $(button_generate).on("api-write:success", (ev, e, payload, response) => {
          var badge = row.find('.status-badge').data("widget");
          badge.load();
        });
      };

      // set up the route server config generator status badge

      this.$w.list.formatters.routeserver_config_status = (value, data, col) => {

        // config is not queued up and has never been generated - badge is empty

        if(!value)
          return $('<span>')

        // config is queued up for generation or has been generated - init badge widget

        var badge = new $ctl.widget.StatusBadge(
          this.$w.list.base_url, $('<span>').data('row-id', data.id).data('name','routeserver_config_status'),
          ["ok","error","cancelled"]
        );

        // need to self reference badge widget so that it can be accessed
        // later if the user manually triggers a config generation

        badge.element.data("widget", badge);

        // render badge

        badge.render(value,data);

        return badge.element;

      };

      this.$w.list.formatters.speed = $ctl.formatters.pretty_speed;

      $(this.$w.list).on("api-read:before",function()  {
        let url = this.base_url.split("/").slice(0,-1);
        url.push($ctl.ixctl.ix_slug());
        this.base_url = url.join("/");
      })

      this.initialize_sortable_headers();

      this.$w.list.load();
    },

    menu : function() {
      const menu = this.Tool_menu();
      menu.find('[data-element="button_add_routeserver"]').click(() => {
        this.create_routeserver();
      });
      menu.find('[data-element="button_list_view"]').click(() => {
        this.view_list();
      });

      return menu;
    },

    sync : function() {
      this.view_list();
      const ix_id = $ctl.ixctl.ix()

      if(ix_id) {
        const exchange = $ctl.ixctl.exchanges[ix_id]
        const rs_namespace = exchange.grainy.replace(/^ix\./, "routeserver.")+".?"
        if(grainy.check(rs_namespace, "r")) {
          this.show();
          this.apply_ordering();
          this.$w.list.load();
          this.$e.menu.find('[data-element="button_api_view"]').attr(
            "href", this.$w.list.base_url + "/" + this.$w.list.action +"?pretty"
          )

          this.$e.menu.find('[data-element="button_add_routeserver"]').grainy_toggle(exchange.grainy, "c");

        } else {
          this.hide();
        }

      } else {
        // no exchanges exist - hide routeservers tool
        this.hide();
      }
    },

    unload_dialog : function() {
      this.$e.body.empty();
      this.view_list()
    },

    format_request_url : function(url) {
      return url.replace("ix_tag", fullctl.ixctl.ix_object().slug);
    },

    create_routeserver : function() {
      // show back to list button
      $(this.$e.menu).find('[data-element="button_list_view"]').show()

      const dialog = this.custom_dialog('Create route server');

      const rs_wiz = new $ctl.widget.Wizard(this.template("routeserver_wizard", dialog));
      this.widget("rs_pdb_list", ($e) => {
        return new twentyc.rest.List(
          this.template("routeserver_pdb_list",
          rs_wiz.element.find('.pdbrouteserver-list'))
        );
      })
      const form = new twentyc.rest.Form(
        this.template("form_routeserver_page", rs_wiz.element.find('.rs-form'))
      );
      const button_delete = form.element.find('[data-element="rs_delete"]');

      const form_defaults = {
        rpki_bgp_origin_validation: true,
        graceful_shutdown: true
      };

      this.$w.rs_pdb_list.format_request_url = this.format_request_url;

      this.$w.rs_pdb_list.formatters.row = (row, data) => {
        row.find('button').click(() =>{
          form.fill(data);
          rs_wiz.set_step(2);
        });
      };

      $(this.$w.rs_pdb_list).on("load:after", () => {
        if(!this.$w.rs_pdb_list.list_body.find('tr.rs-row').length) {
          rs_wiz.set_step(2);
          button_delete.hide();
        }
      });

      this.$w.rs_pdb_list.load();

      form.format_request_url = this.format_request_url;
      form.reset();
      form.fill(form_defaults);

      button_delete.find('span.label').text('Back');
      button_delete.click(() => { rs_wiz.set_step(1); form.reset(); form.fill(form_defaults) });


      $(form).on("api-write:success", (ev, e, payload) => {
        this.sync();
        this.view_list()
      });

    },

    edit_routeserver : function(rs) {
      console.log("editing", rs);

      // show back to list button
      $(this.$e.menu).find('[data-element="button_list_view"]').show()

      const form = new twentyc.rest.Form(
        this.template("form_routeserver_page", this.custom_dialog('Edit '+rs.name))
      );
      const button_delete = new twentyc.rest.Button(
        form.element.find('[data-element="rs_delete"]')
      );
      button_delete.format_request_url = this.format_request_url
      button_delete.action = rs.id;

      form.form_action = String(rs.id);
      form.method = "put";
      form.format_request_url = this.format_request_url;


      $(form).on("api-write:before", (ev, e, payload) => {
        payload["ix"] = rs.ix;
        payload["id"] = rs.id;
      });


      $(form).on("api-write:success", (ev, e, payload) => {
        this.sync();
        this.view_list()
      });

      $(button_delete).on("api-write:success", (ev, e, payload) => {
        fullctl.ixctl.page('routeservers');
        this.sync();
        this.view_list()
      });


      form.fill(rs);

    }

  },
  $ctl.application.Tool
);

$($ctl).on("init_tools", (e, app) => {
  app.tool("routeservers", () => {
    return new $ctl.application.Ixctl.Routeservers();
  })

  $('#tab-routeservers').on('show.bs.tab', () => {
    app.$t.routeservers.sync();
  });
});

})(jQuery, twentyc.cls, fullctl);
