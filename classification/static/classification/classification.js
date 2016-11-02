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
}

function colorToHexString(red, green, blue) {
     red = red.toString(16);
    if(red.length == 1) {
        red = "0" + red;
    }
    green = green.toString(16);
    if(green.length == 1) {
        green = "0" + green;
    }
    blue = blue.toString(16);
    if(blue.length == 1) {
        blue = "0" + blue;
    }
    return '#' + red + green + blue;
}

function addLabelButton(label_id, red, green, blue) {
    var labelButton = {
        id: label_id,
        red: red,
        green: green,
        blue: blue
    };
    labelButtons.push(labelButton);

    console.log(red + green + blue);
    $("#labelButton" + label_id).css("background-color", colorToHexString(red, green, blue));
    $('#labelButton' + label_id).mousedown(function() {
        changeLabel(label_id);
        save();
    });
}

function changeLabel(label_id) {
    for(var i = 0; i < labelButtons.length; i++)  {
        if(labelButtons[i].id == label_id) {
            currentLabel = label_id;
            var label = labelButtons[i]
            // Set correct button to active
            $('#labelButton' + label.id).addClass('activeLabel');
            currentColor = {
                red: label.red,
                green: label.green,
                blue: label.blue
            };
            console.log(i + ' is now active label');
        } else {
            // Set all other buttons to inactive
            $('#labelButton' + labelButtons[i].id).removeClass('activeLabel');
        }
    }
}

