var labelButtons = [];
var currentLabel = -1;
var g_taskID;
var g_imageID;


function sendDataForSave() {
    return $.ajax({
        type: "POST",
        url: "/classification/save/",
        data: {
            image_id: g_imageID,
            task_id: g_taskID,
            label_id: currentLabel,
            quality: $('input[name=quality]:checked').val(),
        },
        dataType: "json" // Need this do get result back as JSON
    });
}

function loadClassificationTask(task_id, image_id) {
    g_taskID = task_id;
    g_imageID = image_id;

    $('#clearButton').click(function() {
        // Reset image quality form
        $('#imageQualityForm input[type="radio"]').each(function(){
            $(this).prop('checked', false);
        });
        // Set all label buttons to inactive
        changeLabel(-1);
    });

    // Modify on click listener for label buttons to trigger save
    for(var i = 0; i < labelButtons.length; ++i) {
        var label_id = labelButtons[i].id;
        $('#labelButton' + label_id).click(function() {
            changeLabel(label_id);
            save();
        });
    }
}
