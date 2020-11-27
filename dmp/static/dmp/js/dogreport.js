
function numberWithCommas(x) {
  return x.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",");
}

function keepChosenOpen (chosen) {
    if (chosen.data("chosen") != undefined){

        // Keep Chosen box open when selecting.
        var _fn = chosen.data("chosen").result_select;
        chosen.data("chosen").result_select = function(evt) {
              evt["metaKey"] = true;
              evt["ctrlKey"] = true;
              chosen.data('chosen').result_highlight.addClass("result-selected");
              return _fn.call(chosen.data('chosen'), evt);
        };
    }
}

// Render status select box as a chosen dropdown
var statusChosen = $('#status').chosen({width:"60%",placeholder_text: "Start typing a status or click to see the list"});

keepChosenOpen(statusChosen);

// Select all for status
$(".select-status").click(function () {
    $('.status option').prop('selected', true);
    $('.status').trigger('chosen:updated')
});

// Deselect all for status
$(".deselect-status").click(function () {
    $('.status option').prop('selected', false);
    $('.status').trigger('chosen:updated')
});


// AJAX request to get the page results.
$('#get_results').click(function () {
    var data_results = $("#results");

    // Make results semi transparent while loading to indicate loading.
    data_results.fadeTo('fast',0.5);

    // Get the data from the form
    var datastring = $("#filterform").serialize();
    var target = "/dmp/project/DOG_report/grant_value_report";
    $.ajax({
        type: "POST",
        url: target,
        data: datastring,
        dataType: "json",
        success: function (returnedData) {
            var results = returnedData;
            if (results.length < 1){
                // No results are returned, hide results table  and display message
                $('#results').html("<h4 class='text-danger'>Your search returned no results, please edit your filters and try again.</h4>")

            }
            else {
                // Handle results


                var i;
                var results_string = "<table class='table table-striped'>";

                // build header
                var header = "<tr> <th>Project Group</th>"
                for (i=0; i < results.years_covered.length; i++){
                    header = header + "<th>" + results.years_covered[i]+ "</th>"
                }
                header = header + "</tr>"

                results_string = results_string + header

                // Build table body
                var body = ""
                for (var group in results.project_groups){
                    var row = "<tr><td>" + group + "</td>"
                    for (var year in results.project_groups[group].values){
                        row = row + "<td>" + numberWithCommas(Math.round(results.project_groups[group].values[year])) + "</td>"
                    }

                    body = body + row
                }

                results_string = results_string + body + "</table>"

                $('#results').html(results_string)
                data_results.fadeTo('fast',1);

            }

        },
        error: function (response) {
            // Handle errors

            $('#results').html("<h4 class='text-danger'>No Results. Make sure you have selected at least one status.</h4>");
            data_results.fadeTo('fast',1);



        }
    })
})