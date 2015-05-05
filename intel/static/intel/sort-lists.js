// Target table by id tableID for sorting	
function sortblacklists(tableID) {

  $("#" + tableID + "Table").tablesorter({
    theme : 'blackice',

    sortList: [
      [0,0],
    ],
    // TODO: This should only be applied for IP addresses
    headers: {
      1: { sorter: 'ipAddress' }
    },

    widthFixed: false,
    headerTemplate: '{content}',
    ignoreCase: true,
    sortInitialOrder: "asc",
    emptyTo: "top",

    initWidgets: true,
    widgets: ['zebra', 'columns', 'filter'],

    widgetOptions: {
      zebra: [
        "ui-widget-content even",
        "ui-state-default odd"],

      uitheme: 'jui',

      columns_tfoot: true,
      columns_thead: true,

      // A filter will be added to the top of each table column.
      filter_columnFilters: true,
      // filter widget: css class applied to the table row containing the filters & the inputs within that row
      filter_cssFilter: "tablesorter-filter",
      filter_ignoreCase: true,
      filter_searchDelay: 300,
      filter_placeholder : { search : 'Filter', select : '' },	      

      resizable: true,
      saveSort: true,

      stickyHeaders: "tablesorter-stickyHeader"
    },

    // return the modified template string
    onRenderTemplate: null, // function(index, template){ return template; },

    // called after each header cell is rendered, use index to target the column customize header HTML
    onRenderHeader: function (index) {
      // the span wrapper is added by default
      $(this).find('div.tablesorter-header-inner').addClass('roundedCorners');
    },

    // function called after tablesorter has completed initialization
    initialized: function (table) {},

    // *** CSS CLASS NAMES ***
    tableClass: 'tablesorter',
    cssAsc: "tablesorter-headerSortUp",
    cssDesc: "tablesorter-headerSortDown",
    cssHeader: "tablesorter-header",
    cssHeaderRow: "tablesorter-headerRow",
    cssIcon: "tablesorter-icon",
    cssChildRow: "tablesorter-childRow",
    cssInfoBlock: "tablesorter-infoOnly",
    cssProcessing: "tablesorter-processing",        

    // *** SELECTORS ***
    // jQuery selectors used to find the header cells.
    selectorHeaders: '> thead th, > thead td',

    // jQuery selector of content within selectorHeaders
    // that is clickable to trigger a sort.
    selectorSort: "th, td",

    // rows with this class name will be removed automatically
    // before updating the table cache - used by "update",
    // "addRows" and "appendCache"
    selectorRemove: "tr.remove-me",

    // *** DEBUGING ***
    // send messages to console
    debug: false
  }).tablesorterPager({
    // target the pager markup - see the HTML block below
    container: $("#" + tableID + "TablePager"),
 
    // output string - default is '{page}/{totalPages}';
    // possible variables:
    // {page}, {totalPages}, {startRow}, {endRow} and {totalRows}
    output: '{startRow} to {endRow} ({totalRows})',
  
    // apply disabled classname to the pager arrows when the rows at
    // either extreme is visible - default is true
    updateArrows: true,
  
    // starting page of the pager (zero based index)
    page: 0,
  
    // Number of visible rows - default is 10
    size: 10,
  
    // Save pager page & size if the storage script is loaded (requires $.tablesorter.storage in jquery.tablesorter.widgets.js)
    savePages : true,

    //defines custom storage key
    storageKey: tableID + 'TablePager',

    // if true, the table will remain the same height no matter how many
    // records are displayed. The space is made up by an empty 
    // table row set to a height to compensate; default is false 
    fixedHeight: true,
  
    // remove rows from the table to speed up the sort of large tables.
    // setting this to false, only hides the non-visible rows; needed
    // if you plan to add/remove rows with the pager enabled.
    // NOTE: Enabling this will break React
    removeRows: false,
  
    // css class names of pager arrows
    // next page arrow
    cssNext: '.next',
    // previous page arrow
    cssPrev: '.prev',
    // go to first page arrow
    cssFirst: '.first',
    // go to last page arrow
    cssLast: '.last',
    // select dropdown to allow choosing a page
    cssGoto: '.gotoPage',
    // location of where the "output" is displayed
    cssPageDisplay: '.pagedisplay',
    // dropdown that sets the "size" option
    cssPageSize: '.pagesize',
    // class added to arrows when at the extremes 
    // (i.e. prev/first arrows are "disabled" when on the first page)
    // Note there is no period "." in front of this class name
    cssDisabled: 'disabled'
  
  });
}

// Extend the themes to change any of the default class names 
$.extend($.tablesorter.themes.jui, {
    // change default jQuery uitheme icons - find the full list of icons
    // here: http://jqueryui.com/themeroller/ (hover over them for their name)
    table: 'ui-widget ui-widget-content ui-corner-all', // table classes
    header: 'ui-widget-header ui-corner-all ui-state-default', // header classes
    icons: 'ui-icon', // icon class added to the <i> in the header
    sortNone: 'ui-icon-carat-2-n-s',
    sortAsc: 'ui-icon-carat-1-n',
    sortDesc: 'ui-icon-carat-1-s',
    active: 'ui-state-active', // applied when column is sorted
    hover: 'ui-state-hover', // hover class
    filterRow: '',
    even: 'ui-widget-content', // even row zebra striping
    odd: 'ui-state-default' // odd row zebra striping
});
