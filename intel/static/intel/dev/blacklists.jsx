String.prototype.capitalizeFirstLetter = function() {
  return this.charAt(0).toUpperCase() + this.slice(1);
}

var BlacklistBox = React.createClass({
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
      <div className="blacklistContent">
        <h1>{this.props.data_type.capitalizeFirstLetter()} blacklists</h1>
        <BlacklistList
	  data={this.state.data}
	  data_type={this.props.data_type}
	/>
	<BlacklistPager data_type={this.props.data_type}/>
        <BlacklistForm
	  data_type={this.props.data_type} 
	  onBlacklistUpdate={this.handleBlacklistUpdate}
	/>
      </div>
    );
  }
});

var BlacklistList = React.createClass({
  render: function() {
    // Map received json data to nodes -> Formatted by BlacklistEntry
    var blacklistNodes = this.props.data.map(function (blacklisted) {
      if ('ip' in blacklisted) { blacklisted.data = blacklisted.ip; }
      else if ('domain' in blacklisted) { blacklisted.data = blacklisted.domain; }
      else { blacklisted.data = "Error: Data type"; }
      return (
        <BlacklistEntry
	  key={blacklisted.data}
          data={blacklisted.data}
          impact={blacklisted.impact}
          comment={blacklisted.comment}
          source={blacklisted.source}
          account={blacklisted.account}
          last_modified={blacklisted.last_modified} >
        </BlacklistEntry>
      );
    });
    return (
      // Return formatted output
      <table className="blacklistList" id={this.props.data_type + "Table"}>
        <thead>
          <tr><th>{this.props.data_type.capitalizeFirstLetter()}</th><th>Impact</th><th>Comment</th><th>Source</th>
	  <th>Modified</th><th>Delete</th></tr>
        </thead>
	<tbody>
          {blacklistNodes}
        </tbody>
      </table>
    );
  }
});

var BlacklistForm = React.createClass({
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
      <form className="blacklistForm" onSubmit={this.handleSubmit}>
        <input type="text" placeholder={data_placeholder} ref="data" />
        <input type="text" placeholder="Impact (10-100 incr of 10)" ref="impact" />
        <input type="text" placeholder="Comment" ref="comment" />
        <input type="text" placeholder="Source of data" ref="source" />
        <input type="submit" value="Update" className="button" />
      </form>
    );
  }
});

var BlacklistEntry = React.createClass({
  render: function() {
    return (
      <tr>
      <td>{this.props.data}</td>
      <td>{this.props.impact}</td>
      <td>{this.props.comment}</td>
      <td>{this.props.source}</td>
      <td>{this.props.last_modified}</td>
      <td><input type="checkbox" value={this.props.data} className="checkbox" /></td>
      </tr>
    );
  }
});

var Comment = React.createClass({
  render: function() {
    return (
      <div className="comment">
        <h2 className="commentAuthor">
          {this.props.author}
        </h2>
        {this.props.children}
      </div>
    );
  }
});

var BlacklistPager = React.createClass({
  render: function() {
    return (
      <div className="pager" id={this.props.data_type + "TablePager"}> 
        <img src="/static/tablesorter/addons/pager/icons/first.png" className="first"/> 
        <img src="/static/tablesorter/addons/pager/icons/prev.png" className="prev"/> 
        <span className="pagedisplay"></span> 
        <img src="/static/tablesorter/addons/pager/icons/next.png" className="next"/> 
        <img src="/static/tablesorter/addons/pager/icons/last.png" className="last"/> 
        <select className="pagesize" title="Select page size" value="10"> 
            <option value="10">10</option> 
            <option value="20">20</option> 
            <option value="30">30</option> 
            <option value="40">40</option> 
        </select>  
        <select className="gotoPage" title="Select page number"></select>
      </div>
    );
  }
});

React.render(
  // Get json from URL, pollInterval = 60 seconds
  <BlacklistBox
    list_url="/intel/list_ip"
    add_url="/intel/add_ip"
    delete_url="/intel/delete_ip"
    data_type="ip"
    pollInterval={60000}
  />,   
  document.getElementById('blacklistIP')
);

React.render(
  // Get json from URL, pollInterval = 30 seconds
  <BlacklistBox
    list_url="/intel/list_domain"
    add_url="/intel/add_domain"
    delete_url="/intel/delete_domain"
    data_type="domain"
    pollInterval={30000}
  />,   
  document.getElementById('blacklistDomain')
);
