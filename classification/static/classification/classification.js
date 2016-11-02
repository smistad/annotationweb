var labelButtons = [];
var currentLabel = 0;
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

function save() {
    var messageBox = document.getElementById("message")
    messageBox.innerHTML = '<span class="info">Please wait while saving..</span>';
    sendDataForSave().done(function(data) {
        console.log("Save done..");
        console.log(data);
        var messageBox = document.getElementById("message")
        if(data.success == "true") {
            messageBox.innerHTML = '<span class="success">Image was saved</span>';
            if(g_returnURL != '') {
                window.location = g_returnURL;
            } else {
                // Refresh page
                location.reload();
            }
        } else {
            messageBox.innerHTML = '<span class="error">Save failed! ' + data.message + '</span>';
        }
        console.log(data.message);
    }).fail(function(data) {
        console.log("Ajax failed");
        var messageBox = document.getElementById("message")
        messageBox.innerHTML = '<span class="error">Save failed!</span>';
    }).always(function(data) {
        console.log("Ajax complete");
    });
    console.log("Save function executed");
}

function loadClassificationTask(task_id, image_id) {
    g_taskID = task_id;
    g_imageID = image_id;
    // This is required due to djangos CSRF protection
    var csrftoken = getCookie('csrftoken');
    $.ajaxSetup({
        beforeSend: function(xhr, settings) {
            if (!csrfSafeMethod(settings.type) && !this.crossDomain) {
                xhr.setRequestHeader("X-CSRFToken", csrftoken);
            }
        }
    });

    $('#saveButton').mousedown(save);
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

