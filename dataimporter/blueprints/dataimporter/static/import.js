(function($) {
    $(document).ready(() => {
        $('.js-fileButton').click(e => {
            var elem = document.getElementById('csv_file');
            if (elem && document.createEvent) {
                var evt = document.createEvent("MouseEvents");
                evt.initEvent("click", true, false);
                elem.dispatchEvent(evt);
            }
        });
        $('form').validationEngine('attach', { promptPosition: "right" });

        var bars =   {};
        var texts = {
            "start-upload": '(1/2) Uploading file, please don\'t close the browser window until it finishes',
            "get-import": '(0/2) Retrieving import information, please wait...',
            "start-import": '(2/2) Importing data... you can close the browser window, the import will continue running in the server.',
            "import-completed": 'Import completed',
            "error": 'Error while importing: '
        };

        function progressHandlingFunction(e, containerId) {
            if (e.lengthComputable) {
                var progress = e.loaded / e.total;
                createProgressBar(containerId).animate(progress);
            }
        };

        function updateMessage(containerId, text, errorCls) {
            if (text) {
                $('#' + containerId).closest('.pb').find('.pb-info').addClass(errorCls).text(text);
            }
        };

        function resetProgressBar(containerId) {
            if (bars[containerId]) {
                bars[containerId].animate(0);
            }
        };

        function createProgressBar(containerId, text, dataset) {
            if (bars[containerId]) {
                updateMessage(containerId, text);
                return bars[containerId];
            }

            var message = text || '';
            var dataset = dataset || '';

            var template = '<div class="row pb">' +
                '<span class="pb-dataset">' + dataset + '</span> - ' +
                '<span class="pb-info">' + message + '</span>' +
                '<div class= "pb-container" id="' + containerId + '"></div>' +
                '</div>';
            $('.row.conf').after($(template).clone());
            var bar = new ProgressBar.Line('#' + containerId, {
                strokeWidth: 4,
                easing: 'easeInOut',
                duration: 1400,
                color: '#1785FB',
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
                from: { color: '#1785FB' },
                to: { color: '#1785FB' },
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
                            updateMessage(containerId, texts['import-completed'], 'success');
                        } else {
                            // something unexpected happened
                            updateMessage(containerId, texts['error'] + data['status'], 'failed');
                        }
                    } else {
                        // rerun in 2 seconds
                        setTimeout(function() {
                            updateProgress(status_url, containerId);
                        }, 2000);
                    }
                })
                .done(function() {

                })
                .fail(function(jqxhr, textStatus, error) {
                    setTimeout(function() {
                        updateProgress(status_url, containerId);
                    }, 2000);

                    var err = textStatus + ", " + error;
                    console.log("Request Failed: " + err);
                })
                .always(function() {

                });
        };

        function listImports() {
            $.getJSON('/imports/', function(data) {
                    for (var key in data) {
                        imports = data[key];
                        imports.forEach(job => {
                            var jobId = getId(job);
                            var containerId = getContainerId(jobId);
                            bars[containerId] = createProgressBar(containerId, texts['get-import'], getFileName(job));
                            resetProgressBar(containerId);
                            updateProgress('/import/' + jobId, containerId);
                        });
                    }
                })
                .done(function() {

                })
                .fail(function(jqxhr, textStatus, error) {
                    var err = textStatus + ", " + error;
                    console.log("Request Failed: " + err);
                })
                .always(function() {

                });
        };

        function getId(job) {
            return job.id;
        };

        function getContainerId(jobId) {
            return '_' + jobId.split('-').join('_');
        };

        function getFileName(job) {
            return job.args.split(',')[1].split("'").join("").replace("]", "").trim()
        };

        function createUniqueID() {
            return 'pb_container' + new Date().getTime();
        };

        $(document).on('submit', 'form', (event) => {
            event.preventDefault();
            var $form = $('form');
            var formData = new FormData($form[0]);
            var csrfToken = $form.find('#csrf_token').val();

            var containerId = createUniqueID();
            bars[containerId] = createProgressBar(containerId, texts['start-upload']);
            resetProgressBar(containerId);

            $.ajaxSetup({
                beforeSend: function(xhr, settings) {
                    if (!/^(GET|HEAD|OPTIONS|TRACE)$/i.test(settings.type) && !this.crossDomain) {
                        xhr.setRequestHeader("X-CSRFToken", csrfToken)
                    }
                }
            });

            $("html, body").animate({ scrollTop: $(document).height() }, "slow");

            // send via ajax this data
            $.ajax({
                url: "/",
                type: "POST",

                // progress handling start
                xhr: function() { // Custom XMLHttpRequest
                    var myXhr = $.ajaxSettings.xhr();
                    if (myXhr.upload) { // Check if upload property exists
                        myXhr.upload.addEventListener('progress', function(e) {
                            progressHandlingFunction(e, containerId);
                        }, false); // For handling the progress of the upload
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

        listImports();
    });
}(jQuery));