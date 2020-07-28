(function($, $tc) {


fullctl = {}

fullctl.template = function(name) {
  return $('[data-template="'+name+'"]').clone().attr("data-template",null);
}

fullctl.application = {}
fullctl.widget = {}
fullctl.formatters = {}

fullctl.formatters.pretty_speed = (value) => {
  if(value >= 1000000)
    value = (value / 1000000).toFixed(2)+"T";
  else if(value >= 1000)
    value = (value / 1000).toFixed(2)+"G";
  else
    value = value+"M";
  return value
}

fullctl.formatters.monitor_status = (value) => {
  if(value == "ok") {
     return $('<span>').addClass('active').text('Active');
  } else if(value == "deactivated") {
     return $('<span>').addClass('inactive').text('Stopped');
  }
  return value
}


fullctl.widget.OrganizationSelect = $tc.extend(
  "OrganizationSelect",
  {
    OrganizationSelect : function(jq) {
      this.Select(jq);
    }
  },
  twentyc.rest.Select
);

fullctl.application.Component = $tc.define(
  "Component",
  {
    Component : function(name) {
      this.name = name;
      this.jquery = $('[data-component="'+name+'"]')
      var elements = this.elements = this.$e = {}
      var templates = this.templates = this.$t = {}

      this.widgets = this.$w = {};

      this.jquery.find('[data-element]').each(function(idx) {
        elements[$(this).data("element")] = $(this);
      });

      this.jquery.find('[data-template]').each(function(idx) {
        templates[$(this).data("template")] = $(this);
      });

      this.wire_elements();
    },

    template : function(name, appendTo) {
      var element = this.$t[name].clone().attr('data-template',null);
      if(appendTo)
        element.appendTo(appendTo)
      return element;
    },

    widget : function(name, fn) {
      fn = fn.bind(this);
      var widget = this.$w[name] = fn(this.$e, this.$t);
      return widget;
    },

    wire_elements : function() {
    }
  }
);

fullctl.application.Modal = $tc.extend(
  "Modal",
  {
    Modal : function(type, title, content) {
      this.Component("modal_"+type)
      this.set_title(title);
      this.set_content(content);
      this.show();
    },
    show : function() {
      this.jquery.modal('show');
    },
    hide : function() {
      this.jquery.modal('hide');
    },
    set_title : function(title) {
      this.jquery.find('.modal-title').text(title);
    },
    set_content : function(content) {
      this.jquery.find('.modal-body').empty().append(content);
    }
  },
  fullctl.application.Component
);


fullctl.application.Tool = $tc.extend(
  "Tool",
  {
    Tool : function(name) {
      this.Component(name);
      this.init();
      this.menu();
      this.active = false;
    },

    init : function() {
    },

    sync : function() {

    },

    menu : function() {
      var menu = this.template("menu")
      console.log(this);
      this.$e.menu.append(menu);
      return menu
    },

    activate : function() {
      this.active = true
    },

    deactivate : function() {
      this.active = false
    }
  },
  fullctl.application.Component
);

fullctl.application.Header = $tc.extend(
  "Header",
  {
    Header : function() {
      this.Component("header");

    },

    wire_elements : function() {

      var header = this;

      this.widget('select_org', ($e) => {
        var w = new twentyc.rest.List($e.select_org);
        var org = $e.select_org.data('org')
        $(w).on("insert:after", (e, row, data) => {
          if(org == data.slug) {
            row.addClass('selected')
            row.find('.manage').click(() => {
              new fullctl.application.Orgctl.PermissionsModal();
            });
          } else {
            row.find('.manage').hide();
            row.click(() => {
              window.location.href = "/"+data.slug+"/"+header.app_slug+"/";
            })
          }
        });
        w.load()

        this.wire_app_switcher();

        return w;
      });
    },

    wire_app_switcher : function() {
      this.widget("app_switcher", ($e) => {
        var others = $e.app_switcher.find('.others')
        var selected = $e.app_switcher.find('.selected')
        selected.click(() => {
          others.show();
          selected.addClass('app_bg muted');
        });
        $(document.body).click(function(e) {
          if( !$(e.target).parent().hasClass('selected') ) {
            others.hide();
            selected.removeClass('app_bg muted');
          }
        });
        return {};
      });
    }
  },
  fullctl.application.Component
);


fullctl.application.Toolbar = $tc.extend(
  "Toolbar",
  {
    Toolbar : function() {
      this.Component("toolbar");
    }
  },
  fullctl.application.Component
);


fullctl.application.Application = $tc.define(
  "Application",
  {
    Application : function(id) {
      this.id = id;
      this.components = this.$c = {
        header : new fullctl.application.Header(),
        toolbar : new fullctl.application.Toolbar(),
        main : new fullctl.application.Component("main")
      }
      this.tools = this.$t = {}
    },

    tool : function(name, fn) {
      fn = fn.bind(this);
      var tool = this.$t[name] = fn()
      return tool;
    },

    sync : function() {
      var i, app = this;
      for(i in this.$t) {
        if(this.$t[i].active) {
          this.$t[i].sync(app);
        }
      }
    }
  }
);


fullctl.application.Orgctl = $tc.extend(
  "Orgctl",
  {

  },
  fullctl.application.Tool
)

fullctl.application.Orgctl.Users = $tc.extend(

  "Users",
  {
    Users : function() {
      this.Component("user_listing");
    },

    wire_elements : function() {
      this.rest_api_list = new twentyc.rest.List(this.jquery);

      this.rest_api_list.formatters.name = function(value, data) {
        return $('<span>').append(
          $('<span>').text(value),
          $('<strong>').text(data.you?" (You)":"")
        );
      }

      this.rest_api_list.formatters.permissions = function(value, data) {
        if(!data.manageable.match(/ud/))
          return;
        var component, editor, widget, container = $('<div>');
        for(component in value) {
          editor = this.template("permissions")
          editor.find('[data-field="component"]').text(component);
          widget = new twentyc.rest.PermissionsForm(editor);
          widget.fill(data);
          widget.fill({component:component});
          widget.set_flag_values(value[component]);
          container.append(editor)
        }
        return container;
      }.bind(this.rest_api_list)


      this.rest_api_list.formatters.row = function(row,data) {
        var manage_container = row.filter('.manage')
        if(data.you)
          row.find('.btn-permissions').attr('disabled', true);
        else if(!data.manageable.match(/[ud]/))
          row.find('.btn-permissions').hide();
        else {
          row.find('.btn-permissions').click(function() {
            if(manage_container.is(':visible'))
              manage_container.hide();
            else
              manage_container.show();
          });
        }
        manage_container.hide();
      }

      this.rest_api_list.load();
    }
  },
  fullctl.application.Component
);

fullctl.application.Orgctl.PermissionsModal = $tc.extend(
  "PermissionsModal",
  {
    PermissionsModal : function() {
      var user_listing = new fullctl.application.Orgctl.Users();
      this.Modal("manage", fullctl.org.name+" User Permissions", user_listing.jquery);
    }
  },
  fullctl.application.Modal
);

})(jQuery, twentyc.cls);
