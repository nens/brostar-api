document.addEventListener('DOMContentLoaded', function() {
    // Get form if it exists on the page
    const form = document.querySelector('form');

    if (form) {
        // Track which tab is active
        const zipTab = document.getElementById('zip-tab');
        const filesTab = document.getElementById('files-tab');

        // Ensure only the appropriate fields are required based on the active tab
        zipTab.addEventListener('shown.bs.tab', function() {
            document.getElementById('zip_file').required = true;
            document.getElementById('xml_file').required = false;
        });

        filesTab.addEventListener('shown.bs.tab', function() {
            document.getElementById('zip_file').required = false;
            document.getElementById('xml_file').required = true;
        });

        // Initial setting based on default active tab
        document.getElementById('zip_file').required = true;
        document.getElementById('xml_file').required = false;

        // Form validation
        form.addEventListener('submit', function(event) {
            let isValid = true;
            let errorMessage = '';

            // Validate file uploads based on active tab
            const activeTab = document.querySelector('.nav-link.active').id;

            if (activeTab === 'zip-tab') {
                const zipFile = document.getElementById('zip_file').files[0];
                if (!zipFile) {
                    errorMessage = 'Please select a zip file to upload.';
                    isValid = false;
                } else if (!zipFile.name.toLowerCase().endsWith('.zip')) {
                    errorMessage = 'Please upload a .zip file.';
                    isValid = false;
                }
            } else if (activeTab === 'files-tab') {
                const xmlFile = document.getElementById('xml_file').files[0];

                if (!xmlFile) {
                    errorMessage = 'XML file is required.';
                    isValid = false;
                } else if (!xmlFile.name.toLowerCase().endsWith('.xml')) {
                    errorMessage = 'Please upload a valid .xml file.';
                    isValid = false;
                }
            }

            // Show error or submit
            if (!isValid) {
                event.preventDefault();
                alert(errorMessage);
            } else {
                // Show loading indicator
                const submitBtn = form.querySelector('button[type="submit"]');
                submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Processing...';
                submitBtn.disabled = true;
            }
        });
    }
});
