(function($) {
    $(document).ready(() => {
        var bars =   {};
        var texts = {
            'start-upload': 'Uploading file, please don\'t close the browser window until it finishes',
            'start-import': 'Importing data, now it\'s safe to close the browser window',
            'import-completed': 'Import completed',
            'error': 'Error while importing: '
        };

        function progressHandlingFunction(e) {
            if (e.lengthComputable) {
                var progress = e.loaded / e.total;
                createProgressBar('pb-container').animate(progress);
            }
        };

        function updateMessage(containerId, text) {
            if (text) {
                $('#' + containerId).closest('.pb').find('.pb-info').text(text);
            }
        };

        function resetProgressBar(containerId) {
            if (bars[containerId]) {
                bars[containerId].animate(0);
            }
        };

        function createProgressBar(containerId, text) {
            if (bars[containerId]) {
                updateMessage(containerId, text);
                return bars[containerId];
            }

            var message = text || '';

            var template = '<div class="row pb">' +
                '<span class="pb-info">' + message + '</span>' +
                '<div class= "pb-container" id="' + containerId + '"></div>' +
                '</div>';
            $('.row.conf').after($(template).clone());
            var bar = new ProgressBar.Line('#' + containerId, {
                strokeWidth: 4,
                easing: 'easeInOut',
                duration: 1400,
                color: '#FFEA82',
                trailColor: '#eee',
                trailWidth: 1,
                svgStyle: { width: '100%', height: '100%' },
                text: {
                    style: {
                        color: '#999',
                        position: 'absolute',
                        right: '0',
                        top: '30px',
                        padding: 0,
                        margin: 0,
                        transform: null
                    },
                    autoStyleContainer: false
                },
                from: { color: '#FFEA82' },
                to: { color: '#ED6A5A' },
                step: (state, bar) => {
                    bar.setText(Math.round(bar.value() * 100) + ' %');
                }
            });

            bar.text.style.fontFamily = '"Raleway", Helvetica, sans-serif';
            bar.text.style.fontSize = '2rem';
            return bar;
        };

        function updateProgress(status_url, containerId) {
            $.getJSON(status_url, function(data) {
                // update UI
                progress = parseFloat(data['current'], 10) / parseFloat(data['total'], 10);
                createProgressBar(containerId, texts['start-import']).animate(progress);
                updateMessage(containerId, texts['start-import']);

                if (data['state'] != 'PENDING' && data['state'] != 'PROGRESS') {
                    if ('result' in data) {
                        // show result
                        updateMessage(containerId, texts['import-completed']);
                    } else {
                        // something unexpected happened
                        updateMessage(containerId, texts['error'] + data['status']);
                    }
                } else {
                    // rerun in 2 seconds
                    setTimeout(function() {
                        updateProgress(status_url, containerId);
                    }, 2000);
                }
            });
        };

        $(document).on('submit', 'form', (event) => {
            event.preventDefault();
            var $form = $('form');
            var formData = new FormData($form[0]);
            var csrfToken = $form.find('#csrf_token').val();

            var containerId = 'pb-container';
            bars[containerId] = createProgressBar(containerId, texts['start-upload']);
            resetProgressBar(containerId)

            $.ajaxSetup({
                beforeSend: function(xhr, settings) {
                    if (!/^(GET|HEAD|OPTIONS|TRACE)$/i.test(settings.type) && !this.crossDomain) {
                        xhr.setRequestHeader("X-CSRFToken", csrfToken)
                    }
                }
            });

            // send via ajax this data
            $.ajax({
                url: "/import/",
                type: "POST",

                // progress handling start
                xhr: function() { // Custom XMLHttpRequest
                    var myXhr = $.ajaxSettings.xhr();
                    if (myXhr.upload) { // Check if upload property exists
                        myXhr.upload.addEventListener('progress', progressHandlingFunction, false); // For handling the progress of the upload
                    } else {
                        console.log("Upload progress is not supported!");
                    }
                    return myXhr;
                },

                // ajax events
                // beforeSend: beforeSendHandler,
                // success: completeHandler,
                // error: errorHandler,
                // progress handling ends

                data: formData,
                cache: false,
                // async: false,
                processData: false,
                contentType: false,
                success: function(data, status, request) {
                    status_url = request.getResponseHeader('Location');
                    resetProgressBar(containerId);
                    updateProgress(status_url, containerId);
                },
                error: function(xhr, ajaxOptions, thrownError) {
                    updateMessage('Error ' + thrownError);
                }
            });
            return false;
        });
    });
}(jQuery));