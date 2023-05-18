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

      // v2 - move ix select to header
      this.$c.header.widget("ix_dropdown", ($e) => {
        const w = new twentyc.rest.List($('.ix-select'));

        $(w).on("insert:after", (e, row, data) => {
          row.attr('data-id', data.id);
          row.find(".manage-ix").click(() => {
            this.select_ix(data.id);
            fullctl.ixctl.page('settings');
          })
          row.find('[data-field="name"]').click(() => {
            this.select_ix(data.id)
          })
          this.urlkeys[data.id] = data.urlkey;
          this.exchanges[data.id] = data;
          this.ix_slugs[data.id] = data.slug;

          this.permission_ui();
        });

        return w;
      });

      // wire event handler for when list of exchanges has been loaded

      $(this.$c.header.$w.ix_dropdown).one("load:after", (ev, response)=> {
        this.select_ix(this.preselect_ix);
        var num_exchanges = response.content.data.length;

        // if theree are multiple exchanges, toggle elements with
        // data-toggled="multiple-exchanges" visible, otherwise hide them

        if(num_exchanges > 1) {
          $('[data-toggled="multiple-exchanges"]').show();
        } else {
          $('[data-toggled="multiple-exchanges"]').hide();
        }
      });

      // wire `Set as default` button

      var button_make_default = new twentyc.rest.Button(
        this.$c.header.$e.button_set_default_ix
      );

      // set the url for the button, replacing __ix_slug__ with the slug of the
      // currently selected exchange

      button_make_default.format_request_url = (url) => {
        return url.replace("__ix_slug__", this.ix_slug());
      };

      // on make default success, notify the user

      $(button_make_default).on("api-write:success", (ev, response) => {
        alert("Default IX set successfully");
      });

      // wire import exchange button that is shown when the organization
      // has no exchanges

      var button_import_ix = $("#no-ix-notify [data-element='button_import_exchange']");
      button_import_ix.click(() => {
        this.prompt_import();
      });

      // load exchanges

      this.$c.header.$w.ix_dropdown.load();

      $(this.$c.header.$e.button_create_ix).click(() => {
        this.prompt_create_exchange();
      });

      $(this.$c.header.$e.button_import_ix).click(() => {
        this.prompt_import();
      });

      this.tool("members_non_active_ports", () => {
        return new $ctl.application.Ixctl.MembersNonActivePorts();
      });

      this.tool("members", () => {
        return new $ctl.application.Ixctl.Members();
      });

      this.tool("routeservers", () => {
        return new $ctl.application.Ixctl.Routeservers();
      });

      $($ctl).trigger("init_tools", [this]);

      this.$t.members_non_active_ports.activate();
      this.$t.members.activate();
      this.$t.routeservers.activate();

    },


    permission_ui : function() {
      let $e = this.$c.header.$e;
      let ix = this.exchanges[this.ix()];
      let org = $ctl.org.id;

      $e.button_create_ix.grainy_toggle(`ix.${org}`, "c");
      $e.button_import_ix.grainy_toggle(`ix.${org}`, "c");
    },

    ix : function() {
      return this.$c.header.$w.ix_dropdown.list_body.find('[data-selected]').attr('data-id');
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

    unload_ix : function(id) {
      delete this.exchanges[id];
      delete this.urlkeys[id];
      delete this.ix_slugs[id];
    },


    select_ix : function(id) {
      let dropdown = this.$c.header.$w.ix_dropdown.list_body;
      dropdown.find('[data-selected]').removeAttr('data-selected');
      if(id) {
        dropdown.find(`[data-id="${id}"]`).attr("data-selected", "");
      } else {
        id = dropdown.find('.ix-item').first().attr("data-id");
        dropdown.find('.ix-item').first().attr("data-selected", "")
      }

      let dropdown_header = this.$c.header.$w.ix_dropdown.list_head;
      dropdown_header.find(".ix-dropdown-label").text(
        dropdown.find("[data-selected]").text()
      );

      const ix = this.exchanges[id];
      if(!ix) {
        $('#no-ix-notify').show();
        $('#app-pages').hide();
        return;
      } else {
        $('#no-ix-notify').hide();
        $('#app-pages').show();
        if(!ix.verified) {
          $('#ix-unverified-notify').show();
        } else {
          $('#ix-unverified-notify').hide();
        }
      }


      this.sync();
      this.sync_url(id);
    },

    sync_url: function(id) {
      const url = new URL(window.location)
      const ix = this.exchanges[id];
      url.pathname = ix ? `/${fullctl.org.slug}/${ix.slug}/` : `/${fullctl.org.slug}/`;

      window.history.pushState({}, '', url);
    },

    refresh : function() {
      return this.refresh_select_ix();
    },

    refresh_select_ix : function() {
      return this.$c.header.$w.ix_dropdown.load();
    },

    prompt_import : function(first_import) {
      return new $ctl.application.Ixctl.ModalImport(first_import);
    },

    prompt_create_exchange : function() {
      return new $ctl.application.Ixctl.ModalCreateIX();
    },

    prompt_update_exchange : function() {
      return new $ctl.application.Ixctl.ModalUpdateIX();
    },

    prompt_delete_exchange : function() {
      return new $ctl.application.Ixctl.ModalDeleteIX();
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
      form.element.find("#pdb_ix_id").select2({
        dropdownParent : $(".modal")[0],
        ajax: {
          url: '/autocomplete/pdb/ix',
          dataType: 'json',
        },
        width: '20em'
      });
      $(document).on('select2:open', () => {
        document.querySelector('.select2-search__field').focus();
      });

      form.wire_submit(this.$e.button_submit);
    }
  },
  $ctl.application.Modal
);




$ctl.application.Ixctl.ModalCreateIX = $tc.extend(
  "ModalCreateIX",
  {
    ModalCreateIX : function() {
      let form = this.form = new twentyc.rest.Form(
        $ctl.template("form_create_ix")
      );

      let modal = this;
      $(this.form).on("api-write:success", function(event, endpoint, payload, response) {
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

$ctl.application.Ixctl.ModalDeleteIX = $tc.extend(
  "ModalDeleteIX",
  {
    ModalDeleteIX : function() {
      let ix = $ctl.ixctl.ix_object();

      var form = this.form = new twentyc.rest.Form(
        $ctl.template("form_delete_ix")
      );
      form.base_url = form.base_url.replace("/default", "/"+ $ctl.ixctl.ix_slug());

      var modal = this;

      $(this.form).on("api-write:success", function(event, endpoint, payload, response) {
        $ctl.ixctl.refresh().then(
          () => {
            $ctl.ixctl.unload_ix(ix.id);
            $ctl.ixctl.select_ix()
          }
        );
        modal.hide();
      });
      this.Modal("continue", `Delete ${ix.name}`, form.element);
      form.wire_submit(this.$e.button_submit);
    }
  },
  $ctl.application.Modal
);

/**
 * Displays modal for editing and creating new InternetExchangeMember
 * objects
 *
 * @class ModalMember
 * @constructor
 * @extends $ctl.application.Modal
 * @namespace $ctl.application.Ixctl
 */

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

      // load select options

      var state_select = new twentyc.rest.Select(
        form.element.find('#member-state')
      )
      state_select.load((member?member.ixf_state:null));

      var type_select = new twentyc.rest.Select(
        form.element.find('#member-type')
      )
      type_select.load((member?member.ixf_member_type:null));

      // setup port auto complete




      fullctl.ext.select2.init_autocomplete(

        // bind to port <select> element
        form.element.find("#port"),

        // parent dropdown to form element
        form.element,

        // options
        {

          // autocomplete url
          url: "/autocomplete/device/port",

          // place holder text for the search field
          placeholder: "Search IP, device, port or location names.",

          // if session is specifed, preselect it's port
          initial: (callback) => {
            if(!member) {
              return null;
            }
            form.get(member.id).then((response,b,c) => {
              let member = response.content.data[0];
              callback({
                id: member.port.id,
                primary: member.port.display_name,
                secondary: member.port.virtual_port_name,
                extra: member.port.device.display_name
              })
            })
          }
        }
      );

      if(member) {
        title = "Edit "+member.display_name;
        form.method = "PUT"
        form.form_action = member.id;
        form.fill(member);

        form.element.find('#member-as-macro').attr('placeholder', member.as_macro)

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

      this.Modal("save_right", title, form.element);
      form.wire_submit(this.$e.button_submit);
    }
  },
  $ctl.application.Modal
);


$ctl.application.Ixctl.MembersNonActivePorts = $tc.extend(
  "MembersNonActivePorts",
  {
    MembersNonActivePorts : function() {
      this.Tool("members-non-active-ports");
    },
    init : function() {
      this.widget("list", ($e) => {
        return new twentyc.rest.List(
          this.template("list", this.$e.body)
        );
      })

      this.$w.list.formatters.row = (row, data) => {

        if (data.port != null) {
          row.hide();
        }

        row.find('a[data-action="edit_member"]').click(() => {
          const member = row.data("apiobject");
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

      this.initialize_sortable_headers();
    },

    menu : function() {
      var menu = this.Tool_menu();
      menu.find('[data-element="button_add_member"]').click(() => {
        return new $ctl.application.Ixctl.ModalMember($ctl.ixctl.ix_slug());
      });

      /**
       * hides members in the UI based on whether the asn matches the
       * `search_term` parameter and scrolls to the first match of the
       * `search_term`
       *
       * @function member_filter
       * @param {String} search_term
       */
      const member_filter = (search_term) => {
        let first_match;
        this.$w.list.load();

        $(this.$w.list).on("load:after", () => {
          const members = this.$w.list.list_body.find("tr:not(.secondary)");

          members.each(function() {
            const primary_row = $(this);
            const secondary_row = $(this).next();

            const asn = $(this).find('[data-field="asn"]').text().toLowerCase();
            if (asn.startsWith(search_term)) {
              primary_row.removeClass("filter-hidden");
              secondary_row.removeClass("filter-hidden");

              if (!first_match) {
                this.scrollIntoView();
                first_match = this;
              }
            } else {
              primary_row.addClass("filter-hidden");
              secondary_row.addClass("filter-hidden");
            }
          });
        });
      }

      /**
       * unhides all hidden members in the UI if they were expanded because of
       * the `member_filter` function.
       *
       * @function clear_member_filter
       */
      const clear_member_filter = () => {
        this.$w.list.list_body.find(".filter-hidden").removeClass("filter-hidden");
      }

      new fullctl.application.Searchbar(
        menu.find(".member-searchbar"),
        member_filter,
        clear_member_filter
      );

      return menu;
    },

    sync : function() {
      var ix_id = $ctl.ixctl.ix()
      if(ix_id) {
        var exchange = $ctl.ixctl.exchanges[ix_id]
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

      this.initialize_sortable_headers();
    },

    menu : function() {
      var menu = this.Tool_menu();
      menu.find('[data-element="button_add_member"]').click(() => {
        return new $ctl.application.Ixctl.ModalMember($ctl.ixctl.ix_slug());
      });

      /**
       * hides members in the UI based on whether the asn matches the
       * `search_term` parameter and scrolls to the first match of the
       * `search_term`
       *
       * @function member_filter
       * @param {String} search_term
       */
      const member_filter = (search_term) => {
        let first_match;
        this.$w.list.load();

        $(this.$w.list).on("load:after", () => {
          const members = this.$w.list.list_body.find("tr:not(.secondary)");

          members.each(function() {
            const primary_row = $(this);
            const secondary_row = $(this).next();

            const asn = $(this).find('[data-field="asn"]').text().toLowerCase();
            if (asn.startsWith(search_term)) {
              primary_row.removeClass("filter-hidden");
              secondary_row.removeClass("filter-hidden");

              if (!first_match) {
                this.scrollIntoView();
                first_match = this;
              }
            } else {
              primary_row.addClass("filter-hidden");
              secondary_row.addClass("filter-hidden");
            }
          });
        });
      }

      /**
       * unhides all hidden members in the UI if they were expanded because of
       * the `member_filter` function.
       *
       * @function clear_member_filter
       */
      const clear_member_filter = () => {
        this.$w.list.list_body.find(".filter-hidden").removeClass("filter-hidden");
      }

      new fullctl.application.Searchbar(
        menu.find(".member-searchbar"),
        member_filter,
        clear_member_filter
      );

      return menu;
    },

    sync : function() {
      var ix_id = $ctl.ixctl.ix()
      if(ix_id) {
        var exchange = $ctl.ixctl.exchanges[ix_id]
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
