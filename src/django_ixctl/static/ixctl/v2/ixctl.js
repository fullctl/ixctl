(function($, $tc, $ctl) {

$ctl.application.Ixctl = $tc.extend(
  "Ixctl",
  {
    Ixctl : function() {
      this.Application("ixctl");

      this.autoload_page();
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

      this.tool("members", () => {
        return new $ctl.application.Ixctl.Members();
      });

      this.tool("member_details", () => {
        return new $ctl.application.Ixctl.MemberDetails();
      })

      this.tool("traffic", () => {
        return new $ctl.application.Ixctl.Traffic();
      });

      $($ctl).trigger("init_tools", [this]);

      this.$t.members.activate();
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
      $ctl.ixctl.$t.traffic.sync();
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
          url: "/autocomplete/device/port?org="+fullctl.org.slug,

          // place holder text for the search field
          placeholder: "Search IP, device, port or location names.",

          // if session is specifed, preselect it's port
          initial: (callback) => {
            if(!member) {
              return null;
            }
            form.get(member.id).then((response,b,c) => {
              let member = response.content.data[0];

              if(!member.port) {
                callback({});
                return;
              }

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


$ctl.application.Ixctl.Members = $tc.extend(
  "Members",
  {
    Members : function() {
      this.Tool("members");
    },
    init : function() {
      this.widget("list", ($e) => {
        return new $ctl.application.Ixctl.MemberList(
          this.template("list", this.$e.body)
        );
      });
      this.$w.list.formatters.row = (row, data) => {
        row.find('a[data-action="edit_member"]').click(() => {
          var member = row.data("apiobject");
          new $ctl.application.Ixctl.ModalMember($ctl.ixctl.ix_slug(), member);
        }).each(function() {
          if(!grainy.check(data.grainy+".?", "u")) {
            $(this).hide()
          }
        });

        row.find('a[data-action="view_member_details"]').click(() => {
          $ctl.ixctl.$t.member_details.show_member(row.data("apiobject").id);
          $ctl.ixctl.page("member");
        })

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

      $(this.$w.list).on("load:after", () => {
        this.update_counts();
      })

      this.initialize_sortable_headers();
    },

    menu : function() {
      const menu = this.Tool_menu();
      menu.find('[data-element="button_add_member"]').click(() => {
        return new $ctl.application.Ixctl.ModalMember($ctl.ixctl.ix_slug());
      });

      // returns a function that will filter the list based on the search term.
      // This structure is needed because the list is loaded asynchronously
      // and we need to wait for it to load before we can filter it. and the
      // event doesn't pass the search term.
      const after_list_load_func = (search_term) => {
        return () => {
          const members = this.$w.list.list_body.find("tr:not(.secondary)");
          let first_match;

          members.each(function() {
            const primary_row = $(this);
            const secondary_row = $(this).next();

            const asn = $(this).find('[data-field="asn"]').text().toLowerCase();
            if (asn.startsWith(search_term)) {
              primary_row.removeClass("filter-hidden");
              secondary_row.removeClass("filter-hidden");

              if (!first_match) {
                primary_row[0].scrollIntoView();
                first_match = this;
              }
            } else {
              primary_row.addClass("filter-hidden");
              secondary_row.addClass("filter-hidden");
            }
          });
        }
      }

      // used to store the last after_list_load_func so we can remove it
      // when the filter is cleared.
      let last_after_load_func;

      const member_filter = (search_term) => {
        if (last_after_load_func) {
          $(this.$w.list).off("load:after", last_after_load_func);
        }

        last_after_load_func = after_list_load_func(search_term);

        $(this.$w.list).on("load:after", last_after_load_func);

        this.$w.list.load();
      }


      const clear_member_filter = () => {
        this.$w.list.list_body.find(".filter-hidden").removeClass("filter-hidden");
        if (last_after_load_func) {
          $(this.$w.list).off("load:after", last_after_load_func);
          last_after_load_func = null;
        }
      }

      new fullctl.application.Searchbar(
        menu.find(".member-searchbar"),
        member_filter,
        clear_member_filter
      );

      const member_list = this.$w.list;
      menu.find("[data-element=filter_non_active_members]").click(function() {
        $(this).toggleClass("active");
        member_list.toggle_non_active_filter();
      });

      menu.find("[data-element=filter_md5_members]").click(function() {
        $(this).toggleClass("active");
        member_list.toggle_md5_filter();
      });

      return menu;
    },

    update_counts : function() {
      const tool = this;
      let non_active_members = 0;
      let non_md5_members = 0;
      this.$w.list.list_body.find("tr:not(.secondary)").each(function() {
        const data = $(this).data("apiobject");
        if (!tool.$w.list.is_member_active(data)) {
          non_active_members += 1;
        }
        if (tool.$w.list.is_member_md5(data)) {
          non_md5_members += 1;
        }
      });

      this.$e.menu.find('[data-element="filter_non_active_members"] .value').text(non_active_members);
      this.$e.menu.find('[data-element="filter_md5_members"] .value').text(non_md5_members);
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
    }

  },
  $ctl.application.Tool
);


$ctl.application.Ixctl.MemberList = $tc.extend(
  "MemberList",
  {
    MemberList : function(jq, filters) {
      this.List(jq);

      this.filter_status = {
        non_active_members : false,
        md5_members : false
      }

    },

    /**
     * hides or shows non active members in the list.
     *
     * @method toggle_non_active_filter
     * @param {Boolean} [active]
     */
    toggle_non_active_filter : function(active = null) {
      const filter_status =  active != null ? active : !this.filter_status.non_active_members;
      this.filter_status.non_active_members = filter_status;

      if (filter_status) {
        $(this).on("insert:after", this.hide_active_members)
      } else {
        $(this).off("insert:after", this.hide_active_members)
      }

      this.load();
    },

    /**
     * Add a class to rows that are not active. This is used to hide them.
     *
     * @method hide_active_members
     * @param {Event} e
     * @param {jQuery} row
     * @param {Object} data
     */
    hide_active_members : function(e, row, data) {
      if (this.is_member_active(data)) {
        row.addClass('filter-non-active-hidden')
      }
    },

    /**
     * Returns true if the member is active.
     *
     * @method is_member_active
     * @param {Object} apiobj
     */
    is_member_active : function(apiobj) {
      return apiobj.ixf_state == "active" || apiobj.port != null;
    },

    /**
     * hides or shows members with md5 activated in the list.
     *
     * @method toggle_md5_filter
     * @param {Boolean} [active]
     */
    toggle_md5_filter : function(active = null) {
      const filter_status =  active != null ? active : !this.filter_status.md5_members;
      this.filter_status.md5_members = filter_status;

      if (filter_status) {
        $(this).on("insert:after", this.hide_non_md5_members)
      } else {
        $(this).off("insert:after", this.hide_non_md5_members)
      }

      this.load();
    },


    /**
     * Add a class to rows that do not have md5. This is used to hide them.
     *
     * @method hide_non_md5_members
     * @param {Event} e
     * @param {jQuery} row
     * @param {Object} data
     */
    hide_non_md5_members : function(e, row, data) {
      if (!this.is_member_md5(data)) {
        row.addClass('filter-non-md5-hidden')
      }
    },

    /**
     * Returns true if the member has md5.
     *
     * @method is_member_md5
     * @param {Object} apiobj
     */
    is_member_md5 : function(apiobj) {
      return apiobj.md5 != null;
    },

  },
  twentyc.rest.List
);


/**
 * Traffic tool
 */


$ctl.application.Ixctl.Traffic = $tc.extend(
  "Traffic",
  {

    Traffic : function() {
      this.Tool("traffic");
    },

    sync : function() {
      this.show_graph_controls().indicate_graph_loading().show_graph()
    },

    // Function to indicate loading
    indicate_graph_loading : function() {
      let graph_container = this.$e.graph_container;
      graph_container.empty().append(fullctl.template("graph_placeholder"));
      return this;
    },

    show_graph_controls() {
      let node = this.$e.graph_container.parents(".ix-total-traffic");
      fullctl.graphs.init_controls(node, this, (end_date, duration)=>{
        this.indicate_graph_loading().show_graph(end_date, duration);
      });
      node.find('.graph-controls').show();
      return this;
    },

    // Function to show graphs
    show_graph : function(end_date, duration) {
      let graph_container = this.$e.graph_container;
      let url = graph_container.data("api-base").replace("/0/", "/"+$ctl.ixctl.ix()+"/")
      let params = [];
      if (end_date) {
        params.push('start_time=' + end_date);
      }
      if (end_date && duration) {
        params.push('duration=' + duration);
      }
      if (params.length > 0) {
        url += '?' + params.join('&');
      }
      fullctl.graphs.render_graph_from_file(
        url,
        ".graph_container",
        fullctl.ixctl.ix_object().name + " Total Traffic",
      ).then(() => {
        // check if a svg has been added to the container, if not, graph data was empty
        if(graph_container.find("svg").length == 0) {
          graph_container.empty().append(
            $('<div class="alert alert-info">').append(
              $('<p>').text("No aggregated traffic data available for this exchange.")
            )
          )
        } else {
          this.$e.refresh_traffic_graph.show();
        }
      })
    }
  },
  $ctl.application.Tool
)

/**
 * Device details tool
 */

$ctl.application.Ixctl.MemberDetails = $tc.extend(
  "MemberDetails",
  {
    MemberDetails: function () {
      this.Tool("member_details");
      this.member_id = 0;
      this.member = null;
    },

    init : function() {

      var tool = this;

      // create member details widget that holds member information
      // such as ip addresses, speed and graphs

      this.widget("member", ($e) => {
        let form = new twentyc.rest.Form(
          this.template("member_widget", this.$e.member_container)
        );
        form.format_request_url = (url) => {
          return url.replace("default", $ctl.ixctl.ix_slug());
        }
        return form;
      });
    },

    // Function to show member details
    show_member : function(member_id) {

      this.member_id = member_id;

      this.$e.graphs_container.empty().append(
        fullctl.template("graph_placeholder")
      );
      this.$e.refresh_traffic_graph.hide();

      this.$w.member.get(""+member_id).then(
        (response) => {
          let member = response.first();
          this.member = member;
          this.$e.menu.find('.member-name').text(member.name);
          this.$e.menu.find('.member-asn').text(member.asn);

          member.virtual_port_name = member.port ? member.port.virtual_port_name :"No port assigned";
          member.device_name = member.port ? member.port.device_name :"";
          member.pretty_speed = fullctl.formatters.pretty_speed(member.speed);
          member.as_macro_prepared = member.as_macro_override || member.as_macro || "";

          this.$e.menu.find('.ip4').text(member.ipaddr4);
          this.$w.member.fill(member);
          this.$e.body.parents(".tool").find('#date_range_select').val("24");
          this.show_graph_controls(member).indicate_graph_loading().show_graphs(member);
        }
      )

    },

    // Function to indicate loading
    indicate_graph_loading : function() {
      let graph_container = this.$e.body.parents(".tool").find("[data-element=graphs_container]");
      graph_container.empty().append(fullctl.template("graph_placeholder"));
      return this;
    },

    show_graph_controls : function(member) {
      let node = this.$e.body.parents(".tool");

      node.data("graph-member", member);

      if(!this.graph_controls_initialized) {
        fullctl.graphs.init_controls(node, this, (end_date, duration)=>{

          this.indicate_graph_loading().show_graphs(node.data("graph-member"), end_date, duration);
        }, "member_graph_");
        this.graph_controls_initialized = true;
      }
      node.find('.graph-controls').show();
      return this;
    },

    hide_graph_controls : function() {
      let node = this.$e.body.parents(".tool");
      node.find('.graph-controls').hide();
    },

    // Function to show graphs
    show_graphs : function(member, end_date, duration) {
      let graph_container = this.$e.body.parents(".tool").find("[data-element=graphs_container]");

      if(!member.port) {
        // member does not have a port assigned
        // display a message and return

        let message = $('<div class="alert alert-info">').append(
          $('<p>').text("This member does not have a port assigned.")
        )
        graph_container.empty().append(message);
        return;
      }

      let url = this.$w.member.element.data('api-traffic-base').replace(/0/g, member.port.virtual_port);
      let params = [];
      if (end_date) {
        params.push('start_time=' + end_date);
      }
      if (end_date && duration) {
        params.push('duration=' + duration);
      }
      if (params.length > 0) {
        url += '?' + params.join('&');
      }

      fullctl.graphs.render_graph_from_file(
        url,
        "#member_port_traffic_graph",
        member.port.virtual_port_name,
      ).then(() => {
        // check if a svg has been added to the container, if not, graph data was empty
        if(graph_container.find("svg").length == 0) {
          graph_container.empty().append(
            $('<div class="alert alert-info">').append(
              $('<p>').text("No traffic data available for this member.")
            )
          )
        } else {
          this.$e.refresh_traffic_graph.show();
        }
      })
    }
  },
  $ctl.application.Tool
);


$(document).ready(function() {
  $ctl.ixctl = new $ctl.application.Ixctl();


  $('#traffic-tab').on('show.bs.tab', () => {
    $ctl.ixctl.$t.traffic.sync();
  });
});


})(jQuery, twentyc.cls, fullctl);
