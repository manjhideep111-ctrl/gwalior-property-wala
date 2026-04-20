// ============================================================
//  Gwalior Property Wala — Google Apps Script
//  Yeh script Google Sheets mein leads save karegi
// ============================================================

function doPost(e) {
  try {
    var ss    = SpreadsheetApp.openById("1hFR1dn_e74ajEOf8zdz8t2daaeWV1_I4fErJlxpI_R4");
    var sheet = ss.getSheetByName("Leads");

    // Agar Leads sheet nahi hai toh banao
    if (!sheet) {
      sheet = ss.insertSheet("Leads");
      sheet.appendRow(["Date", "Name", "Phone", "Requirement", "Source", "Chat ID", "Status"]);
      
      // Header styling
      var header = sheet.getRange(1, 1, 1, 7);
      header.setBackground("#1a1a2e");
      header.setFontColor("#ffffff");
      header.setFontWeight("bold");
    }

    var data = JSON.parse(e.postData.contents);

    sheet.appendRow([
      data.date        || new Date().toLocaleString("en-IN"),
      data.name        || "Not Provided",
      data.phone       || "Not Provided",
      data.requirement || "General Enquiry",
      data.source      || "Telegram Bot",
      data.chat_id     || "",
      data.status      || "New Lead"
    ]);

    // Auto-color new lead row
    var lastRow = sheet.getLastRow();
    sheet.getRange(lastRow, 7).setBackground("#90EE90"); // Green for New Lead

    return ContentService
      .createTextOutput(JSON.stringify({ status: "success", message: "Lead saved!" }))
      .setMimeType(ContentService.MimeType.JSON);

  } catch (err) {
    return ContentService
      .createTextOutput(JSON.stringify({ status: "error", message: err.toString() }))
      .setMimeType(ContentService.MimeType.JSON);
  }
}


// ============================================================
//  Properties Sheet Setup — Pehli baar manually run karo
// ============================================================
function setupPropertiesSheet() {
  var ss    = SpreadsheetApp.openById("1hFR1dn_e74ajEOf8zdz8t2daaeWV1_I4fErJlxpI_R4");
  var sheet = ss.getSheetByName("Properties");

  if (!sheet) {
    sheet = ss.insertSheet("Properties");
  }

  // Headers
  sheet.getRange(1, 1, 1, 6).setValues([
    ["Location", "Type", "Price", "Size", "Features", "Status"]
  ]);

  // Sample data
  var sampleData = [
    ["Morar Colony",  "2BHK Flat",           "28 Lakh",  "900 sqft",  "Lift, Parking, Gated Society",        "Available"],
    ["Thatipur",      "3BHK Flat",           "46 Lakh",  "1400 sqft", "Fully Furnished, Modular Kitchen",    "Available"],
    ["Hazira",        "1BHK Flat",           "12 Lakh",  "550 sqft",  "Ready to Move, Near Market",          "Available"],
    ["Madhoganj",     "Villa 4BHK",          "85 Lakh",  "2500 sqft", "Garden, 2 Parking, CCTV",             "Available"],
    ["Lashkar",       "Residential Plot",    "15 Lakh",  "100 Gaj",   "Corner Plot, Main Road",              "Available"],
    ["City Center",   "Commercial Shop",     "38 Lakh",  "300 sqft",  "Ground Floor, Heavy Footfall",        "Available"],
    ["Sipri Bazaar",  "Office Space",        "18 Lakh",  "500 sqft",  "2nd Floor, AC, Parking",              "Available"],
    ["Bahodapur",     "Residential Plot",    "22 Lakh",  "150 Gaj",   "All Facilities Nearby",               "Available"],
  ];

  sheet.getRange(2, 1, sampleData.length, 6).setValues(sampleData);

  // Header styling
  var header = sheet.getRange(1, 1, 1, 6);
  header.setBackground("#16213e");
  header.setFontColor("#ffffff");
  header.setFontWeight("bold");

  Logger.log("✅ Properties sheet setup complete!");
}


// ============================================================
//  Test Function — Manually run karke check karo
// ============================================================
function testLeadSave() {
  var ss    = SpreadsheetApp.openById("1hFR1dn_e74ajEOf8zdz8t2daaeWV1_I4fErJlxpI_R4");
  var sheet = ss.getSheetByName("Leads");

  if (!sheet) {
    sheet = ss.insertSheet("Leads");
    sheet.appendRow(["Date", "Name", "Phone", "Requirement", "Source", "Chat ID", "Status"]);
  }

  sheet.appendRow([
    new Date().toLocaleString("en-IN"),
    "Test Customer",
    "9876543210",
    "2BHK Flat in Morar",
    "Test",
    "12345",
    "New Lead"
  ]);

  Logger.log("✅ Test lead saved successfully!");
}
