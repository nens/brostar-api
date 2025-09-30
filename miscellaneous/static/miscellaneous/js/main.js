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
            document.getElementById('shp_file').required = false;
            document.getElementById('shx_file').required = false;
        });

        filesTab.addEventListener('shown.bs.tab', function() {
            document.getElementById('zip_file').required = false;
            document.getElementById('shp_file').required = true;
            document.getElementById('shx_file').required = true;
        });

        // Initial setting based on default active tab
        document.getElementById('zip_file').required = true;
        document.getElementById('shp_file').required = false;
        document.getElementById('shx_file').required = false;

        // Form validation
        form.addEventListener('submit', function(event) {
            const kvkNumber = document.getElementById('kvk_number').value.trim();
            let isValid = true;
            let errorMessage = '';

            // Validate KVK number (basic validation)
            if (!kvkNumber) {
                errorMessage = 'KVK number is required.';
                isValid = false;
            } else if (!/^\d{8}$/.test(kvkNumber)) {
                errorMessage = 'KVK number should be 8 digits.';
                isValid = false;
            }

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
                const shpFile = document.getElementById('shp_file').files[0];
                const shxFile = document.getElementById('shx_file').files[0];

                if (!shpFile) {
                    errorMessage = 'SHP file is required.';
                    isValid = false;
                } else if (!shpFile.name.toLowerCase().endsWith('.shp')) {
                    errorMessage = 'Please upload a valid .shp file.';
                    isValid = false;
                }

                if (!shxFile) {
                    errorMessage = 'SHX file is required.';
                    isValid = false;
                } else if (!shxFile.name.toLowerCase().endsWith('.shx')) {
                    errorMessage = 'Please upload a valid .shx file.';
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
