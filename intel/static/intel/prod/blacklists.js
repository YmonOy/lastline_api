String.prototype.capitalizeFirstLetter = function() {
  return this.charAt(0).toUpperCase() + this.slice(1);
}

var BlacklistBox = React.createClass({displayName: "BlacklistBox",
  // Loads blacklist data from server
  loadBlacklistFromServer: function() {
    $.ajax({
      url: this.props.list_url,
      dataType: 'json',
      success: function(data) {
        this.setState({data: data});
	// Update table sort after changes (TableSorter)
	$("#" + this.props.data_type + "Table").trigger("updateAll").trigger("appendCache").trigger("applyWidgets");
      }.bind(this),
      error: function(xhr, status, err) {
        //console.error(this.props.url, status, err.toString());
        alert("Error: Connection to API failed.");
      }.bind(this)
    });
  },

  // Submits changes to server
  handleBlacklistUpdate: function(blacklistUpdate) {
    // Optimistic submission, add entry already on js side
    // this is so that we do not have to wait for server reply -> Snappy.
    var blacklisted = this.state.data;
    //var newBlacklists = blacklisted.concat([blacklistUpdate.add]);
    //this.setState({data: newBlacklists});

    if ('add' in blacklistUpdate) {
      $.ajax({
        url: this.props.add_url,
        dataType: 'json',
        type: 'POST',
	// Without JSON.stringify this would be POST: ip=1.1.1.1&comment=bla..
        data: { entries: JSON.stringify([blacklistUpdate.add]) },
        success: function(data) {
	  if (data['errors'].length) {
            // TODO: Better error reporting
            alert("API says:" + JSON.stringify(data));
	  } 
          // We could just set state here if we changed it in JS.
          //this.setState({data: data}); 
          this.loadBlacklistFromServer(); // Refresh blacklist from server
        }.bind(this),
        error: function(xhr, status, err) {
          //console.error(this.props.url, status, err.toString());
          alert("Error: Connection to API failed.");
        }.bind(this)
      });
    }

    if ('deletes' in blacklistUpdate) {
      $.ajax({
        url: this.props.delete_url,
        dataType: 'json',
        type: 'POST',
        data: { entries: JSON.stringify(blacklistUpdate.deletes) },
        success: function(data) {
	  if (data['errors'].length) {
            // TODO: Better error reporting
            alert("API says:" + JSON.stringify(data));
	  }

          else {
            // Remove the removed entries from our data, otherwise we end up
	    // desynching with the dom information React thinks should be there.
	    // This is a problem with TableSorter modifying dom outside React.
  	    filter_fn = function(filter_array, filter_by) {
	      return(function(x) {
                return(filter_array.filter(function(y) {
                  return(y == x[filter_by]);
                }).length == 0);
              });
            }(blacklistUpdate.deletes, this.props.data_type); 

	    var blacklistFiltered = blacklisted.filter(filter_fn);

	    // TODO: Both needed until we have better solution
            //this.setState({data: blacklistFiltered}); // Update internal state
            //this.replaceState({data: blacklistFiltered}); // Update internal state
	    //this.forceUpdate();
            //this.loadBlacklistFromServer(); // Refresh blacklist from server
	  
	    // TODO: TableSorter still explodes us on removal of entry, may need to
	    // consider alternative to TableSorter or figure out something lighter to
	    // do here.
	    window.location.reload();
	  }

        }.bind(this),
        error: function(xhr, status, err) {
          //console.error(this.props.url, status, err.toString());
          alert("Error: Connection to API failed.");
        }.bind(this)
      });
    }

  },
  getInitialState: function() {
    return {data: []};
  },
  componentDidMount: function() {
    this.loadBlacklistFromServer();
    // TODO: Autoupdates disabled until table paging retains state.
    //setInterval(this.loadBlacklistFromServer, this.props.pollInterval);

    // Initialize table sorting for our table (Can be empty here too.)
    // Argument is the Table ID
    sortblacklists(this.props.data_type); 
  },
  render: function() {
    return (
      React.createElement("div", {className: "blacklistContent"}, 
        React.createElement("h1", null, this.props.data_type.capitalizeFirstLetter(), " blacklists"), 
        React.createElement(BlacklistList, {
	  data: this.state.data, 
	  data_type: this.props.data_type}
	), 
	React.createElement(BlacklistPager, {data_type: this.props.data_type}), 
        React.createElement(BlacklistForm, {
	  data_type: this.props.data_type, 
	  onBlacklistUpdate: this.handleBlacklistUpdate}
	)
      )
    );
  }
});

var BlacklistList = React.createClass({displayName: "BlacklistList",
  render: function() {
    // Map received json data to nodes -> Formatted by BlacklistEntry
    var blacklistNodes = this.props.data.map(function (blacklisted) {
      if ('ip' in blacklisted) { blacklisted.data = blacklisted.ip; }
      else if ('domain' in blacklisted) { blacklisted.data = blacklisted.domain; }
      else { blacklisted.data = "Error: Data type"; }
      return (
        React.createElement(BlacklistEntry, {
	  key: blacklisted.data, 
          data: blacklisted.data, 
          impact: blacklisted.impact, 
          comment: blacklisted.comment, 
          source: blacklisted.source, 
          account: blacklisted.account, 
          last_modified: blacklisted.last_modified}
        )
      );
    });
    return (
      // Return formatted output
      React.createElement("table", {className: "blacklistList", id: this.props.data_type + "Table"}, 
        React.createElement("thead", null, 
          React.createElement("tr", null, React.createElement("th", null, this.props.data_type.capitalizeFirstLetter()), React.createElement("th", null, "Impact"), React.createElement("th", null, "Comment"), React.createElement("th", null, "Source"), 
	  React.createElement("th", null, "Modified"), React.createElement("th", null, "Delete"))
        ), 
	React.createElement("tbody", null, 
          blacklistNodes
        )
      )
    );
  }
});

var BlacklistForm = React.createClass({displayName: "BlacklistForm",
  handleSubmit: function(e) {
    // Prevents automatic browser submit by the user action,
    // data submission is handled by our code instead.
    e.preventDefault();

    // Build entry add/update from browser input
    var data = this.refs.data.getDOMNode().value.trim();
    var impact = this.refs.impact.getDOMNode().value.trim();
    var comment = this.refs.comment.getDOMNode().value.trim();
    var source = this.refs.source.getDOMNode().value.trim();
    if (data && impact && comment && source) {
      var update = {add: {impact: impact, comment: comment, source: source}}
      // Handle different KEY for types here
      // TODO: This should not be an if conditional
      if (this.props.data_type == 'ip') {
	$.extend(update.add, {ip: data});
      }
      else if (this.props.data_type == 'domain') { 
        $.extend(update.add, {domain: data});
      }
      // Fills properties for our submit code
      this.props.onBlacklistUpdate(update);

      // Clear input fields, TODO: better way to iterate?
      this.refs.data.getDOMNode().value = '';
      this.refs.impact.getDOMNode().value = '';
      this.refs.comment.getDOMNode().value = '';
      this.refs.source.getDOMNode().value = '';
    }


    // Iterate deletes from all class .checkbox under .blacklistForm class
    var deletes = []
    $('.blacklistList').find('.checkbox').each(function() {
      if (this.checked) { deletes.push(this.value) }
    })
    if (deletes.length) { 
      this.props.onBlacklistUpdate({deletes: deletes})
    }
  },
  render: function() {
    var data_placeholder = "Add " + this.props.data_type + " entry"
    return (
      React.createElement("form", {className: "blacklistForm", onSubmit: this.handleSubmit}, 
        React.createElement("input", {type: "text", placeholder: data_placeholder, ref: "data"}), 
        React.createElement("input", {type: "text", placeholder: "Impact (10-100 incr of 10)", ref: "impact"}), 
        React.createElement("input", {type: "text", placeholder: "Comment", ref: "comment"}), 
        React.createElement("input", {type: "text", placeholder: "Source of data", ref: "source"}), 
        React.createElement("input", {type: "submit", value: "Update", className: "button"})
      )
    );
  }
});

var BlacklistEntry = React.createClass({displayName: "BlacklistEntry",
  render: function() {
    return (
      React.createElement("tr", null, 
      React.createElement("td", null, this.props.data), 
      React.createElement("td", null, this.props.impact), 
      React.createElement("td", null, this.props.comment), 
      React.createElement("td", null, this.props.source), 
      React.createElement("td", null, this.props.last_modified), 
      React.createElement("td", null, React.createElement("input", {type: "checkbox", value: this.props.data, className: "checkbox"}))
      )
    );
  }
});

var Comment = React.createClass({displayName: "Comment",
  render: function() {
    return (
      React.createElement("div", {className: "comment"}, 
        React.createElement("h2", {className: "commentAuthor"}, 
          this.props.author
        ), 
        this.props.children
      )
    );
  }
});

var BlacklistPager = React.createClass({displayName: "BlacklistPager",
  render: function() {
    return (
      React.createElement("div", {className: "pager", id: this.props.data_type + "TablePager"}, 
        React.createElement("img", {src: "/static/tablesorter/addons/pager/icons/first.png", className: "first"}), 
        React.createElement("img", {src: "/static/tablesorter/addons/pager/icons/prev.png", className: "prev"}), 
        React.createElement("span", {className: "pagedisplay"}), 
        React.createElement("img", {src: "/static/tablesorter/addons/pager/icons/next.png", className: "next"}), 
        React.createElement("img", {src: "/static/tablesorter/addons/pager/icons/last.png", className: "last"}), 
        React.createElement("select", {className: "pagesize", title: "Select page size", value: "10"}, 
            React.createElement("option", {value: "10"}, "10"), 
            React.createElement("option", {value: "20"}, "20"), 
            React.createElement("option", {value: "30"}, "30"), 
            React.createElement("option", {value: "40"}, "40")
        ), 
        React.createElement("select", {className: "gotoPage", title: "Select page number"})
      )
    );
  }
});

React.render(
  // Get json from URL, pollInterval = 60 seconds
  React.createElement(BlacklistBox, {
    list_url: "/intel/list_ip", 
    add_url: "/intel/add_ip", 
    delete_url: "/intel/delete_ip", 
    data_type: "ip", 
    pollInterval: 60000}
  ),   
  document.getElementById('blacklistIP')
);

React.render(
  // Get json from URL, pollInterval = 30 seconds
  React.createElement(BlacklistBox, {
    list_url: "/intel/list_domain", 
    add_url: "/intel/add_domain", 
    delete_url: "/intel/delete_domain", 
    data_type: "domain", 
    pollInterval: 30000}
  ),   
  document.getElementById('blacklistDomain')
);
