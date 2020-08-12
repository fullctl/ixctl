(function(twentyc, $) {

/**
 * jquery function for closest descendant
 * credit: https://stackoverflow.com/a/8962023
 */

(function($) {
    $.fn.closest_descendant = function(filter) {
        var $found = $(),
            $currentSet = this.children(); // Current place
        while ($currentSet.length) {
            $found = $currentSet.filter(filter);
            if ($found.length) break;  // At least one match: break loop
            // Get all children of the current set
            $currentSet = $currentSet.children();
        }
        return $found.first(); // Return first match of the collection
    }
})(jQuery);

/**
 * namespace for twentyc.rest
 */

twentyc.rest = {

  /**
   * object holding global config
   * @type Object
   * @name config
   * @namespace twentyc.rest
   */

  config : {

    /**
     * set this to the CSRF token that should
     * be sent with write requests to the API
     * if any
     *
     * @type String
     * @name csrf
     * @namespace twentyc.rest.config
     */

    csrf : ""
  }
}

/**
 * Wrapper for API responses
 * @class Response
 * @constructor
 * @namespace twentyc.rest
 * @param {XHR Response} response
 * @param {Number} status
 */

twentyc.rest.Response = twentyc.cls.define(
  "Response",
  {

    Response : function(response, status) {
      if(!response || (!response.data && !response.errors) ) {
        this.status = status;
        return;
      }
      this.content = response;
    },

    rows : function(callback) {
      var i;
      for(i = 0; i < this.content.data.length; i++) {
        callback(this.content.data[i], i)
      }
    },

    first : function() {
      if(this.content && this.content.data) {
        return this.content.data[0];
      }
      return null;
    },

    field_errors : function(callback) {
      if(!this.has_errors())
        return

      var key;
      for(key in this.content.errors) {
        if(key == "non_field_errors")
          continue;

        callback(key, this.content.errors[key])
      }
    },

    non_field_errors : function(callback) {
      if(!this.has_errors())
        return

      var nfe = this.content.errors.non_field_errors;

      if(typeof nfe == "string")
        nfe = [nfe];

      if(nfe) {
        var i;
        callback(nfe)
      }

    },

    http_status_text : function() {
      if(this.status == 401) return "Unauthorized Access";
      if(this.status == 403) return "Permission Denied";
      if(this.status == 404) return "Resource not found";
      if(this.status == 405) return "Method not allowed";
      if(this.status == 500) return "Internal Error";
      return "Http Error "+this.status;
    },

    has_errors : function() {
      if(this.status > 400) {
        if(!this.content)
          this.content = {}
        if(!this.content.errors)
          this.content.errors = {}

        this.content.errors.non_field_errors =  [this.http_status_text()]
      }
      return ($.isEmptyObject(this.content.errors) == false);
    }
  }
);

twentyc.rest.Client = twentyc.cls.define(
  "Client",
  {
    Client : function(base_url) {
      this.base_url = base_url.replace(/\/$/g,'');
    },

    endpoint_url : function(endpoint) {
      if(!endpoint)
        return this.base_url+"/";
      return this.base_url+"/"+endpoint + "/";
    },

    encode : function(data) {
      return JSON.stringify(data);
    },

    read : function(endpoint, data, method) {
      method = method.toLowerCase()
      $(this).trigger("api-request:before", [endpoint,data,method])
      $(this).trigger("api-read:before", [endpoint,data,method])
      $(this).trigger("api-"+method+":before", [endpoint,data])
      var request = new Promise(function(resolve, reject) {
        $.ajax({
          method : method.toUpperCase(),
          data : data,
          url : this.endpoint_url(endpoint),
        }).done(function(result) {
          var response = new twentyc.rest.Response(result);
          $(this).trigger("api-request:success", [endpoint, data, response, method]);
          $(this).trigger("api-read:success", [endpoint, data, response, method]);
          $(this).trigger("api-"+method+":success", [endpoint, data, response]);
          resolve(response);
        }.bind(this)).fail(function(e) {
          var response = new twentyc.rest.Response(e.responseJSON);
          $(this).trigger("api-request:error", [endpoint, data, response, method]);
          $(this).trigger("api-read:error", [endpoint, data, response, method]);
          $(this).trigger("api-"+method+":error", [endpoint, data, response]);
          reject(response);
        }.bind(this)).always(function(e) {
          $(this).trigger("api-request:after", [endpoint, data, method]);
          $(this).trigger("api-read:after", [endpoint, data, method]);
          $(this).trigger("api-"+method+":after", [endpoint, data]);
        }.bind(this));
      }.bind(this));

      return request;
    },

    write : function(endpoint, data, method) {
      method = method.toLowerCase();
      $(this).trigger("api-request:before", [endpoint,data,method])
      $(this).trigger("api-write:before", [endpoint,data,method])
      $(this).trigger("api-"+method+":before", [endpoint,data])
      var request = new Promise(function(resolve, reject) {
        $.ajax({
          dataType : "json",
          method : method.toUpperCase(),
          url : this.endpoint_url(endpoint),
          data : this.encode(data),
          headers : {
            "Content-Type" : "application/json",
            "X-CSRFToken" : twentyc.rest.config.csrf
          },
        }).done(function(result) {
          var response = new twentyc.rest.Response(result);
          $(this).trigger("api-request:success", [endpoint, data, response, method]);
          $(this).trigger("api-write:success", [endpoint, data, response, method]);
          $(this).trigger("api-"+method+":success", [endpoint, data, response]);
          resolve(response);
        }.bind(this)).fail(function(e) {
          var response = new twentyc.rest.Response(e.responseJSON, e.status);
          $(this).trigger("api-request:error", [endpoint, data, response, method]);
          $(this).trigger("api-write:error", [endpoint, data, response, method]);
          $(this).trigger("api-"+method+":error", [endpoint, data, response]);
          reject(response);
        }.bind(this)).always(function(e) {
          $(this).trigger("api-request:after", [endpoint, data, method]);
          $(this).trigger("api-write:after", [endpoint, data, method]);
          $(this).trigger("api-"+method+":after", [endpoint, data]);
        }.bind(this));
      }.bind(this));

      return request;
    },

    get : function(endpoint, params) {
      return this.read(endpoint, params, "get");
    },

    post : function(endpoint, data) {
      return this.write(endpoint, data, "post");
    },

    put : function(endpoint, data) {
      return this.write(endpoint, data, "put");
    },

    delete : function(endpoint, data) {
      return this.write(endpoint, data, "delete");
    }
  }
);

twentyc.rest.Widget = twentyc.cls.extend(
  "Widget",
  {
    Widget : function(base_url, jq) {
     this.action = jq.data("api-action")
     this.local_actions = {}
     this.Client(base_url);
     this.bind(jq);
    },

    start_processing : function() {
      this.busy = true
      if(!this.loading_shim) {
        this.loading_shim = $('<div>').addClass("loading-shim")
        this.element.append(this.loading_shim);
      }
      this.loading_shim.show();
      $(this).trigger("processing");
    },

    done_processing : function() {
      this.busy = false
      if(this.loading_shim && !window.debug_loading_shim)
        this.loading_shim.hide();
      $(this).trigger("ready");
    },

    template : function(name) {
      var tmpl = this.element.closest_descendant('.templates').find('[data-template="'+name+'"]')
      var clone = tmpl.clone().attr('data-template', null);
      return clone;
    },

    bind : function(jq) {
      jq.data("rest_widget", this);
      this.element = jq;

      this.redirect = this.element.data("api-redirect")

      $(this).on("api-write:before", function() {
        this.clear_errors();
        this.start_processing();
      }.bind(this));

      $(this).on("api-write:after", function() {
        this.done_processing();
      }.bind(this));

      $(this).on("api-read:before", function() {
        this.start_processing();
      }.bind(this));

      $(this).on("api-read:after", function() {
        this.done_processing();
      }.bind(this));


    },

    local_action : function(name, fn) {
      this.local_actions[name] = fn;
    },

    clear_errors : function() {
      this.element.find('.validation-error').detach();
      this.element.find('.validation-error-indicator').removeClass("validation-error-indicator");
    },

    render_error : function(key, errors) {
      var i, e;
      var error_node = $('<div>').addClass("validation-error");
      var input = this.element.find('[name="'+key+'"]');
      input.addClass("validation-error-indicator")
      for(i = 0; i < errors.length; i++) {
        error_node.append($('<p>').text(errors[i]))
      }
      if(input.attr("type") != "checkbox")
        error_node.insertAfter(input);
    },

    render_non_field_errors : function(errors) {
      var error_node = $('<div>').addClass("alert alert-danger validation-error");
      for(i = 0; i < errors.length; i++) {
        error_node.append($('<div>').text(errors[i]))
      }
      this.element.prepend(error_node)
    },

    payload : function() {
      var data = {};
      this.element.find('[data-api-submit="yes"]').each(function() {
        $(this).find("input,select,textarea").each(function() {
          var input = $(this)
          if(input.attr("type") == "checkbox") {
            if(input.prop("checked"))
              data[input.attr("name")] = true;
            else
              data[input.attr("name")] = false;
          } else {
            data[input.attr("name")] = input.val();
          }
        });
      });
      return data;

    },


  },
  twentyc.rest.Client
);


twentyc.rest.Form = twentyc.cls.extend(
  "Form",
  {
    Form : function(jq) {
      var base_url = jq.data("api-base")
      this.form_action = jq.data("api-action")
      this.Widget(base_url, jq);
    },

    fill : function(data) {
      var key, value;
      for(key in data) {
        value = data[key];
        this.element.find('[name="'+key+'"]').each(function() {
          if($(this).attr("type") == "checkbox") {
            $(this).prop("checked", value);
          } else {
            $(this).val(value);
          }
        });
      }
    },

    post_success : function(result) {

    },

    post_failure : function(response) {
      response.field_errors(this.render_error.bind(this));
      response.non_field_errors(this.render_non_field_errors.bind(this))
    },

    submit : function(method) {
      this.clear_errors();

      if(!method)
        method = this.method

      var fn = this[method.toLowerCase()].bind(this);
      fn(this.form_action, this.payload()).then(
        this.post_success.bind(this),
        this.post_failure.bind(this)
      );
    },

    bind : function(jq) {
      this.Widget_bind(jq);
      this.method = jq.data("api-method") || "POST";

      this.element.find('input,textarea').keydown(function(event){
        if(event.keyCode == 13) {
          event.preventDefault();
          this.submit();
          return false;
        }
      }.bind(this));

      var widget = this;

      this.element.find('button.submit').click(function() {
        widget.submit(
          $(this).data("api-method")
        );
      });
    },

    wire_submit : function(jq_button) {
      var widget = this;
      jq_button.off("click").click(function() {
        widget.submit($(this).data("api-method"))
      });
    }
  },
  twentyc.rest.Widget
);

twentyc.rest.Select = twentyc.cls.extend(
  "Select",
  {
    Select : function(jq) {
      var base_url = jq.data("api-base")
      this.load_action = jq.data("api-load")
      this.name_field = jq.data("name-field") || "name"
      this.id_field = jq.data("id-field") || "id"
      this.selected_field = jq.data("selected-field") || "selected"
      this.Widget(base_url, jq);
    },

    payload: function() {
      return { "id": this.element.val() }
    },

    post_success : function(result) {

    },

    post_failure : function(response) {
      response.field_errors(this.render_error.bind(this));
      response.non_field_errors(this.render_non_field_errors.bind(this))
    },


    load : function(select_this) {

      return this.get().then(function(response) {
        var select = this.element;
        var name_field = this.name_field
        var id_field = this.id_field
        var selected_field = this.selected_field
        select.empty()
        $(response.content.data).each(function() {
          var selected = this[selected_field] || false;
          var opt = $('<option>').val(this[id_field]).text(this[name_field])
          if(selected)
            opt.attr("selected", true);
          select.append(opt);
        });

        $(this).trigger("load:after", [select, response.content.data]);
      }.bind(this));
    },

    refresh : function() {
      var val = this.element.val()
      return this.load().then(
       () => { this.element.val(val); },
       () => {}
      );
    },

    bind : function(jq) {
      this.Widget_bind(jq);
      this.method = jq.data("api-method") || "POST";

      if(this.load_action)
        this.load();

      this.element.on("change", function() {
        this.clear_errors();

        if(!this.action)
          return;

        var fn = this[this.method.toLowerCase()].bind(this);
        fn(this.action, this.payload()).then(
          this.post_success.bind(this),
          this.post_failure.bind(this)
        );
      }.bind(this));
    }
  },
  twentyc.rest.Widget
);

twentyc.rest.List = twentyc.cls.extend(
  "List",
  {
    List : function(jq) {
      var base_url = jq.data("api-base")

      this.id_field = "id"
      this.formatters = {}

      this.Widget(base_url, jq);
    },

    load : function() {
      return this.get(this.action, this.payload()).then(function(response) {
        this.list_body.empty()
        response.rows(function(row, idx) {
          this.insert(row);
        }.bind(this));
        $(this).trigger("load:after");
        return
      }.bind(this));
    },

    insert : function(data) {
      var toggle, k, row_element, col_element;

      row_element = this.template('row')

      for(k in data) {
        var val, formatter = this.formatters[k];
        col_element = row_element.find('[data-field="'+k+'"]')
        toggle = col_element.data("toggle")
        if(toggle) {
          if(data[k]) {
            col_element.addClass(toggle);
          } else {
            col_element.removeClass(toggle);
          }
        } else if(!formatter) {
          col_element.text(data[k])
        } else {
          val = formatter(data[k], data, col_element)
          col_element.empty().append(val)
        }
      }

      if(this.formatters.row)
        this.formatters.row(row_element, data)

      row_element.data("apiobject", data);
      row_element.addClass("row-"+data[this.id_field])

      this.list_body.append(row_element)
      this.wire(row_element)

      $(this).trigger("insert:after", [row_element, data]);
    },

    api_callback_remove : function(response) {
      response.rows(function(row) {
        this.remove(row)
      }.bind(this));
    },

    remove : function(data) {
      $(this).trigger("remove:before", [data]);
      this.list_body.find('.row-'+data[this.id_field]).detach();
    },

    find_row : function(id) {
      return this.list_body.find('.row-'+id);
    },

    action_failure : function(response) {
      response.field_errors(this.render_error.bind(this));
      response.non_field_errors(this.render_non_field_errors.bind(this))
    },

    wire : function(row) {
      var widget = this;

      row.find('a[data-action]').click(function() {
        var actionName = $(this).data("action")
        if(widget.local_actions[actionName]) {
          widget.local_actions[actionName](row.data("apiobject"), row);
        }
      });

      row.find('a[data-api-action], button[data-api-action]').each(function() {
        var method = ($(this).data("api-method") || "POST").toLowerCase();
        var action = $(this).data("api-action").toLowerCase();
        var callback = $(this).data("api-callback");
        var confirm_set = $(this).data("confirm")

        if(callback)
          callback = widget["api_callback_"+callback].bind(widget)

        $(this).click(function() {
          if(confirm_set && !confirm(confirm_set))
            return;
          var apiobj = row.data("apiobject")
          var _action = action.replace(
            /\{([^\{\}]+)\}/,
            (match, p1, offset, string) => {
              return apiobj[p1];
            }
          )
          var request = widget[method](_action, row.data("apiobject")).then(
            callback, widget.action_failure.bind(widget)
          );
        });
      });
    },

    bind : function(jq) {
      this.Widget_bind(jq);

      this.list_body = jq.find(".list-body")
    }
  },
  twentyc.rest.Widget
);


twentyc.rest.PermissionsForm = twentyc.cls.extend(
  "PermissionsForm",
  {
    set_flag_values : function(flags) {
      var form = this;
      this.element.find('input[data-permission-flag]').each(function() {
        var flag_name = $(this).data("permission-flag")
        var value = (flags.indexOf(flag_name) > -1)
        $(this).prop("checked", value)
      });
    },

    payload : function() {
      var payload = this.Form_payload();
      payload.permissions = ""
      this.element.find('input[data-permission-flag]').each(function() {
        if($(this).prop("checked"))
          payload.permissions += $(this).data("permission-flag")
      });

      return payload;
    },

    bind : function(jq) {
      this.Widget_bind(jq);
      this.method = jq.data("api-method") || "POST";
      this.element.find('input[data-permission-flag]').on("change", function() {
        this.clear_errors();
        var fn = this[this.method.toLowerCase()].bind(this);
        fn(this.action, this.payload()).then(
          this.post_success.bind(this),
          this.post_failure.bind(this)
        );
      }.bind(this));

    }
  },
  twentyc.rest.Form
);





})(twentyc, jQuery);
