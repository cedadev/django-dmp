function downloadCSV(csv, filename) {
    var csvFile;
    var downloadLink;

    // CSV file
    csvFile = new Blob([csv], {type: "text/csv"});

    // Download link
    downloadLink = document.createElement("a");

    // File name
    downloadLink.download = filename;

    // Create a link to the file
    downloadLink.href = window.URL.createObjectURL(csvFile);

    // Hide download link
    downloadLink.style.display = "none";

    // Add the link to DOM
    document.body.appendChild(downloadLink);

    // Click download link
    downloadLink.click();
}

function makeRow(JSON){
    var results_array = [];
    for (var programme in JSON){
        var row = [];
        row.push(programme)

        for (var year in JSON[programme].values) {

            row.push(Math.round(JSON[programme].values[year]))
        }

        results_array.push(row.join(","));
    }
    return results_array
}

function objToStr(object, key){
    return [object[key]].join(',')
}

function jsonToCSV(JSON, filename){
    var csv = [];

    // Build Header
    csv.push("Grant Programme," + objToStr(JSON,'years_covered'))

    // Push results
    csv = csv.concat(makeRow(JSON.project_groups))

    downloadCSV(csv.join("\n"), filename)

}

function exportResltsToCSV(form_id, target_url, filename) {

    // Get the data from the form
    var datastring = $("#" + form_id).serialize();

    $.ajax({
        type: "POST",
        url: target_url,
        data: datastring,
        dataType: "json",
        success: function(data) {
            jsonToCSV(data, filename)
        }
    })
}