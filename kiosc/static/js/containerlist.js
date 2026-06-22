let containerlistDT = new DataTable("#kiosc-containerlist-table", {
  responsive: true,
  layout: {
    topStart: "info",
    topEnd: {
      search: {
        text: 'Filter: _INPUT_',
      },
    },
    bottomStart: "pageLength",
    bottomEnd: "paging",
  },
});
