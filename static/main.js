function say_hi(elt) {
    console.log("Welcome to", elt.innerText);
}

say_hi(document.querySelector("h1"));

function make_table_sortable(table) {
    // Find sortable headers (those with sort-column class)
    const sortableHeaders = table.querySelectorAll("th.sort-column");
    
    // If no headers have the sort-column class, default to the last header only
    // (This maintains backward compatibility with Phase 2)
    if (sortableHeaders.length === 0) {
        const headerRow = table.querySelector("thead tr");
        if (!headerRow) return; // Exit if there's no header row
        
        const headers = headerRow.querySelectorAll("th");
        if (headers.length === 0) return; // Exit if there are no header cells
        
        const lastHeaderCell = headers[headers.length - 1];
        makeHeaderSortable(lastHeaderCell, table);
    } else {
        // Otherwise, make all headers with sort-column class sortable
        sortableHeaders.forEach(header => makeHeaderSortable(header, table));
    }
}

function makeHeaderSortable(headerCell, table) {
    // Track sort state for this header
    let sortState = "unsorted"; // can be "unsorted", "asc", or "desc"
    
    // Add click event listener
    headerCell.addEventListener("click", function() {
        // Get the column index
        const columnIndex = headerCell.cellIndex;
        
        // Get all sortable headers in this table
        const allSortableHeaders = table.querySelectorAll("th.sort-column");
        const headerList = allSortableHeaders.length > 0 ? 
                          allSortableHeaders : 
                          table.querySelectorAll("th");
        
        // Remove sort classes from all headers
        headerList.forEach(header => {
            header.classList.remove("sort-asc", "sort-desc");
        });
        
        // Update sort state
        if (sortState === "unsorted") {
            sortState = "asc";
            headerCell.classList.add("sort-asc");
        } else if (sortState === "asc") {
            sortState = "desc";
            headerCell.classList.add("sort-desc");
        } else {
            sortState = "unsorted";
            // No class needed for unsorted
        }
        
        // Get tbody and rows
        const tbody = table.querySelector("tbody");
        if (!tbody) return; // Exit if there's no tbody
        
        const rows = Array.from(tbody.querySelectorAll("tr"));
        
        // Sort the rows
        if (sortState === "unsorted") {
            // Sort by original order (data-index attribute)
            rows.sort(function(rowA, rowB) {
                const indexA = parseInt(rowA.getAttribute("data-index") || "0");
                const indexB = parseInt(rowB.getAttribute("data-index") || "0");
                return indexA - indexB;
            });
        } else {
            // Sort by column value
            rows.sort(function(rowA, rowB) {
                // Get the cell in each row at the specified column index
                let cellA, cellB;
                
                // For last column compatibility with Phase 2
                if (columnIndex === headerList.length - 1) {
                    cellA = rowA.querySelector("td:last-child");
                    cellB = rowB.querySelector("td:last-child");
                } else {
                    // Get by index for other columns
                    const cellsA = rowA.querySelectorAll("td");
                    const cellsB = rowB.querySelectorAll("td");
                    if (columnIndex < cellsA.length) cellA = cellsA[columnIndex];
                    if (columnIndex < cellsB.length) cellB = cellsB[columnIndex];
                }
                
                if (!cellA || !cellB) return 0;
                
                // Get the values to compare
                let valueA, valueB;
                
                // Try to use data-value attribute if it exists
                if (cellA.hasAttribute("data-value") && cellB.hasAttribute("data-value")) {
                    const dataA = cellA.getAttribute("data-value");
                    const dataB = cellB.getAttribute("data-value");
                    
                    // Try to convert to numbers if possible
                    const numA = parseFloat(dataA);
                    const numB = parseFloat(dataB);
                    
                    if (!isNaN(numA) && !isNaN(numB)) {
                        valueA = numA;
                        valueB = numB;
                    } else {
                        valueA = dataA;
                        valueB = dataB;
                    }
                } else {
                    // Fallback to text content
                    const textA = cellA.textContent.trim();
                    const textB = cellB.textContent.trim();
                    
                    // Parse numeric values (handle percentages and fractions)
                    const numA = parseFloat(textA);
                    const numB = parseFloat(textB);
                    
                    if (!isNaN(numA) && !isNaN(numB)) {
                        valueA = numA;
                        valueB = numB;
                    } else {
                        valueA = textA;
                        valueB = textB;
                    }
                }
                
                // Sort in the appropriate direction
                if (sortState === "asc") {
                    if (typeof valueA === "number" && typeof valueB === "number") {
                        return valueA - valueB;
                    } else {
                        return String(valueA).localeCompare(String(valueB));
                    }
                } else { // sortState === "desc"
                    if (typeof valueA === "number" && typeof valueB === "number") {
                        return valueB - valueA;
                    } else {
                        return String(valueB).localeCompare(String(valueA));
                    }
                }
            });
        }
        
        // Clear the tbody
        while (tbody.firstChild) {
            tbody.removeChild(tbody.firstChild);
        }
        
        // Re-insert the sorted rows
        rows.forEach(function(row) {
            tbody.appendChild(row);
        });
    });
}

// Grade hypothesizing functionality
function make_grade_hypothesized(table) {
    // Create the "Hypothesize" button
    const button = document.createElement('button');
    button.textContent = 'Hypothesize';
    button.style.marginBottom = '1rem';
    
    // Insert the button before the table
    table.parentNode.insertBefore(button, table);
    
    // Add click listener to the button
    button.addEventListener('click', function() {
        if (table.classList.contains('hypothesized')) {
            // Switch back to actual grades
            table.classList.remove('hypothesized');
            button.textContent = 'Hypothesize';
            restoreOriginalGrades(table);
        } else {
            // Switch to hypothesized grades
            table.classList.add('hypothesized');
            button.textContent = 'Actual grades';
            setupHypotheticalInputs(table);
        }
        
        // Update the final grade
        updateFinalGrade(table);
    });
}

function setupHypotheticalInputs(table) {
    // Find all cells with "Not Due" or "Ungraded" and replace with inputs
    const cells = table.querySelectorAll('td.number');
    
    cells.forEach(cell => {
        const text = cell.textContent.trim();
        
        if (text === 'Not Due' || text === 'Ungraded') {
            // Store original text
            cell.setAttribute('data-original-text', text);
            
            // Create input element
            const input = document.createElement('input');
            input.type = 'number';
            input.min = '0';
            input.max = '100';
            input.step = '0.1';
            input.style.width = '4rem';
            
            // Add keyup event listener to update grade when typing
            input.addEventListener('keyup', function() {
                updateFinalGrade(table);
            });
            
            // Clear cell and append input
            cell.textContent = '';
            cell.appendChild(input);
        }
    });
}

function restoreOriginalGrades(table) {
    // Find all inputs in cells and restore original text
    const inputs = table.querySelectorAll('td.number input');
    
    inputs.forEach(input => {
        const cell = input.parentNode;
        const originalText = cell.getAttribute('data-original-text');
        
        if (originalText) {
            cell.textContent = originalText;
        }
    });
}

function updateFinalGrade(table) {
    const isHypothesized = table.classList.contains('hypothesized');
    const rows = table.querySelectorAll('tbody tr');
    let totalWeight = 0;
    let earnedPoints = 0;
    
    // Process each assignment row
    rows.forEach(row => {
        const cells = row.querySelectorAll('td');
        if (cells.length < 2) return; // Skip rows without enough cells
        
        const statusCell = cells[1];
        const status = statusCell.textContent.trim();
        
        // Get assignment weight from data attribute
        const weight = parseInt(row.getAttribute('data-weight') || "0");
        
        // Skip if no weight
        if (!weight) return;
        
        let percentage = null;
        
        // If hypothesized mode and there's an input, use its value
        if (isHypothesized && statusCell.querySelector('input')) {
            const input = statusCell.querySelector('input');
            if (input.value) {
                percentage = parseFloat(input.value);
            }
        } 
        // For actual grades or non-input cells
        else if (status.endsWith('%')) {
            percentage = parseFloat(status);
        } else if (status === 'Missing') {
            percentage = 0;
        }
        
        // For any assignment with a grade (real or hypothesized)
        if (percentage !== null) {
            totalWeight += weight;
            earnedPoints += (percentage / 100) * weight;
        }
    });
    
    // Compute the final grade
    let finalGrade = 0;
    if (totalWeight > 0) {
        finalGrade = (earnedPoints / totalWeight) * 100;
    }
    
    // Update the final grade in the footer
    const footer = table.querySelector('tfoot');
    if (footer) {
        const gradeCell = footer.querySelector('td.number strong');
        if (gradeCell) {
            gradeCell.textContent = finalGrade.toFixed(1) + '%';
        }
    }
}

// Asynchronous form submission function
function make_form_async(form) {
    form.addEventListener("submit", async function(event) {
        // Prevent the default form submission
        event.preventDefault();
        
        console.log("Async form submission started");
        
        // Create a FormData object from the form
        const formData = new FormData(form);
        
        // Get the CSRF token
        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
        
        try {
            // Send the form data asynchronously using fetch
            const response = await fetch(form.action, {
                method: form.method,
                body: formData,
                headers: {
                    'X-CSRFToken': csrfToken
                },
                credentials: 'same-origin'
            });
            
            console.log("Response received:", response.status);
            
            // Create or get the status message element
            let statusMessage = form.querySelector('.upload-status');
            if (!statusMessage) {
                statusMessage = document.createElement('p');
                statusMessage.className = 'upload-status';
                form.appendChild(statusMessage);
            }
            
            if (response.ok) {
                // Success - display success message
                statusMessage.textContent = "Upload succeeded";
                statusMessage.style.color = "green";
                
                console.log("Upload successful, reloading page in 1.5 seconds");
                
                // Reload the page after a short delay to show the new submission status
                setTimeout(() => {
                    window.location.reload();
                }, 1500);
            } else {
                // Error - display error message
                statusMessage.textContent = "Upload failed. Please try again.";
                statusMessage.style.color = "red";
                console.log("Upload failed with status:", response.status);
            }
        } catch (error) {
            // Network or other error
            console.error("Error during fetch:", error);
            
            let statusMessage = form.querySelector('.upload-status');
            if (!statusMessage) {
                statusMessage = document.createElement('p');
                statusMessage.className = 'upload-status';
                form.appendChild(statusMessage);
            }
            
            statusMessage.textContent = "Error: " + error.message;
            statusMessage.style.color = "red";
        }
    });
}

// When the page loads, initialize everything
document.addEventListener("DOMContentLoaded", function() {
    console.log("DOM loaded, initializing JS features");
    
    // Handle sortable tables
    const sortableTables = document.querySelectorAll("table.sortable");
    console.log("Found", sortableTables.length, "sortable tables");
    sortableTables.forEach(make_table_sortable);
    
    // Look for a submission form on the assignment page
    const submissionForm = document.querySelector('form[enctype="multipart/form-data"]');
    if (submissionForm) {
        console.log("Found submission form, making it async");
        make_form_async(submissionForm);
    }
    
    // Set up hypothesized grades on profile page for students
    if (window.location.pathname.includes('/profile')) {
        console.log("On profile page, looking for grades table");
        const profileTable = document.querySelector('table.sortable');
        if (profileTable) {
            console.log("Found profile grades table, adding hypothesize functionality");
            make_grade_hypothesized(profileTable);
        } else {
            console.log("No sortable table found on profile page");
        }
    }
});