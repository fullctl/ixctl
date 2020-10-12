(function($, $tc, $ctl) {
$ctl.application.Ixctl.Networks = $tc.extend(
  "Networks",
  {
    Networks : function() {
      this.urlparam = "asn"
      this.TabbedTool("nets");
    },
    init : function() {

      var tool = this;

      this.widget("list", ($e) => {
        return new twentyc.rest.List(
          this.template("list", this.$e.body)
        );
      })

      this.$w.list.formatters.row = (row, data) => {
        if(data.access) {
          row.find('a[data-api-action="permreq/"]').hide()
        }
      }

      this.$w.list.formatters.access = (value, data) => {
        if(value == "denied") {
          return $("<a>").attr("tabindex",0).text("Request Access").
            click(() => {
              tool.request_access(data)
            })
        }
        if(value == "pending") {
          return "Pending"
        }
        if(value == "view") {
          return $("<a>").attr("href", "/"+data.org+"/?ix="+data.ix).text(
            "View AS"+data.asn+" at "+data.ix_name
          )
        }
        if(value == "manage") {
          return $("<a>").attr("href", "/"+data.org+"/?ix="+data.ix).text(
            "Manage AS"+data.asn+" at "+data.ix_name
          )
        }

        return value

      }

    },

    request_access : function(presence) {
      return new $ctl.application.Ixctl.ModalPermissionRequest(presence)
    },

    menu : function() {
      var menu = this.TabbedTool_menu();
      return menu;
    },

    sync : function() {
    },

    tab : function(tab, data) {
      this.TabbedTool_tab(tab, data)
      this.$w.list.base_url = this.$w.list.base_url.replace(
        /\/\d+$/,
        "/"+data.asn
      )
      this.$w.list.load()
    }
  },
  $ctl.application.TabbedTool
);

$ctl.application.Ixctl.ModalPermissionRequest = $tc.extend(
  "ModalPermissionRequest",
  {
    ModalPermissionRequest : function(presence) {
      var form = this.form = new twentyc.rest.Form(
        $ctl.template("form_permreq")
      );
      var modal = this;

      form.base_url = form.base_url.replace("__org__", presence.org);
      $(this.form).on("api-write:success", function(event, endpoint, payload, response) {
        $ctl.ixctl.$t.networks.$w.list.load();
        modal.hide();
      });
      this.Modal("continue", "Request Access from "+presence.org_name, form.element);
      form.wire_submit(this.$e.button_submit);
    }
  },
  $ctl.application.Modal
);



$($ctl).on("init_tools", (e, app) => {
  app.tool("networks", () => {
    return new $ctl.application.Ixctl.Networks();
  })
});



})(jQuery, twentyc.cls, fullctl);
