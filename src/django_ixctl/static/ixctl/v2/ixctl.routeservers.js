(function($, $tc, $ctl) {

$ctl.application.Ixctl.Routeservers = $tc.extend(
  "Routeservers",
  {
    Routeservers : function() {
      this.Tool("routeservers");
      this.activate();
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
          fullctl.ixctl.page("settings");
          fullctl.ixctl.$t.settings.edit_routeserver(routeserver);
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
    },

    menu : function() {
      var menu = this.Tool_menu();
      menu.find('[data-element="button_add_routeserver"]').click(() => {
        fullctl.ixctl.page("settings");
        fullctl.ixctl.$t.settings.create_routeserver();
      });
      return menu;
    },

    sync : function() {
      var ix_id = $ctl.ixctl.ix()
      if(ix_id) {
        var exchange = $ctl.ixctl.exchanges[ix_id]
        var rs_namespace =exchange.grainy.replace(/^ix\./, "routeserver.")+".?"
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
