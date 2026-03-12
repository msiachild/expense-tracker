function doPost(e) {

  var sheet = SpreadsheetApp.getActiveSpreadsheet().getSheets()[0];

  var data = JSON.parse(e.postData.contents);

  sheet.appendRow([
    data.date,
    data.category,
    data.item,
    data.amount
  ]);

  return ContentService.createTextOutput("Success");

}
