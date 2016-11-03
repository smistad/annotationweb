
function sendDataForSave() {
    return $.ajax({
        type: "POST",
        url: "/classification/save/",
        data: {
            image_id: g_imageID,
            task_id: g_taskID,
            label_id: g_currentLabel,
            quality: $('input[name=quality]:checked').val(),
        },
        dataType: "json" // Need this do get result back as JSON
    });
}

function loadClassificationTask() {

    $('#clearButton').click(function() {
        g_annotationHasChanged = true;
        // Reset image quality form
        $('#imageQualityForm input[type="radio"]').each(function(){
            $(this).prop('checked', false);
        });
        // Set all label buttons to inactive
        changeLabel(-1);
    });

    // Add click listener for label buttons to trigger save
    for(var i = 0; i < g_labelButtons.length; ++i) {
        var label_id = g_labelButtons[i].id;
        $('#labelButton' + label_id).click(function() {
            save();
        });
    }
}
