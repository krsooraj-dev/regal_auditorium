// File: js/script.js

document.addEventListener('DOMContentLoaded', function () {
    // 1. Mobile Menu Toggle
    const navToggle = document.getElementById('mobile-nav-toggle');
    const mainNav = document.getElementById('main-nav');
    
    if (navToggle && mainNav) {
        navToggle.addEventListener('click', function () {
            mainNav.classList.toggle('open');
            // Toggle hamburger icon state
            const spans = navToggle.querySelectorAll('span');
            if (mainNav.classList.contains('open')) {
                spans[0].style.transform = 'rotate(45deg) translate(6px, 6px)';
                spans[1].style.opacity = '0';
                spans[2].style.transform = 'rotate(-45deg) translate(5px, -6px)';
            } else {
                spans[0].style.transform = 'none';
                spans[1].style.opacity = '1';
                spans[2].style.transform = 'none';
            }
        });
    }

    // 2. Alert/Notification Banner Helper
    function showNotification(message, type = 'success') {
        // Check if banner already exists
        let banner = document.getElementById('notify-banner');
        if (!banner) {
            banner = document.createElement('div');
            banner.id = 'notify-banner';
            banner.className = 'notify-banner';
            document.body.appendChild(banner);
        }
        
        banner.textContent = message;
        banner.className = `notify-banner show ${type}`;
        
        setTimeout(() => {
            banner.classList.remove('show');
        }, 4000);
    }

    // 3. Availability Calendar Logic
    const calendarContainer = document.getElementById('calendar-display');
    const monthYearTitle = document.getElementById('current-month-year');
    const prevMonthBtn = document.getElementById('prev-month-btn');
    const nextMonthBtn = document.getElementById('next-month-btn');
    
    let currentDate = new Date();
    // Anchor to May 2026 for simulation if needed, but let's use the actual date
    // User metadata says current local time is May 2026.
    
    if (calendarContainer && monthYearTitle) {
        let currentYear = currentDate.getFullYear();
        let currentMonth = currentDate.getMonth(); // 0-indexed
        
        // Render initially
        loadAndRenderCalendar(currentYear, currentMonth);
        
        if (prevMonthBtn && nextMonthBtn) {
            prevMonthBtn.addEventListener('click', function () {
                currentMonth--;
                if (currentMonth < 0) {
                    currentMonth = 11;
                    currentYear--;
                }
                loadAndRenderCalendar(currentYear, currentMonth);
            });
            
            nextMonthBtn.addEventListener('click', function () {
                currentMonth++;
                if (currentMonth > 11) {
                    currentMonth = 0;
                    currentYear++;
                }
                loadAndRenderCalendar(currentYear, currentMonth);
            });
        }
    }
    
    async function loadAndRenderCalendar(year, month) {
        monthYearTitle.textContent = new Date(year, month).toLocaleDateString('en-IN', { year: 'numeric', month: 'long' });
        
        // Fetch booked dates from FastAPI
        let availabilityData = {};
        try {
            const response = await fetch(`/api/availability?year=${year}&month=${month + 1}`);
            if (response.ok) {
                const resJson = await response.json();
                availabilityData = resJson.data || {};
            }
        } catch (err) {
            console.error("Failed to load availability data from server:", err);
            // Fallback to empty if server fails
        }
        
        renderCalendarGrid(year, month, availabilityData);
    }
    
    function renderCalendarGrid(year, month, availability) {
        calendarContainer.innerHTML = '';
        
        // Add Weekday Headers
        const weekdays = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
        weekdays.forEach(day => {
            const header = document.createElement('div');
            header.className = 'day-header';
            header.textContent = day;
            calendarContainer.appendChild(header);
        });
        
        const firstDayIndex = new Date(year, month, 1).getDay();
        const totalDays = new Date(year, month + 1, 0).getDate();
        
        // Add empty cells for preceding days
        for (let i = 0; i < firstDayIndex; i++) {
            const emptyCell = document.createElement('div');
            emptyCell.className = 'day-cell empty';
            calendarContainer.appendChild(emptyCell);
        }
        
        const today = new Date();
        
        // Add calendar day cells
        for (let day = 1; day <= totalDays; day++) {
            const dateStr = `${year}-${String(month + 1).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
            const cell = document.createElement('div');
            cell.className = 'day-cell';
            
            const numSpan = document.createElement('span');
            numSpan.className = 'day-number';
            numSpan.textContent = day;
            cell.appendChild(numSpan);
            
            // Check status in DB response
            let status = availability[dateStr] || 'available'; // Default is available
            cell.classList.add(status);
            
            const labelSpan = document.createElement('span');
            labelSpan.className = 'day-status-label';
            labelSpan.textContent = status;
            cell.appendChild(labelSpan);
            
            // Highlight today
            if (today.getFullYear() === year && today.getMonth() === month && today.getDate() === day) {
                cell.classList.add('today');
            }
            
            // Add click action for available cells
            if (status === 'available') {
                cell.addEventListener('click', function () {
                    // Preselect date on booking form
                    const dateInput = document.getElementById('event-date');
                    if (dateInput) {
                        dateInput.value = dateStr;
                        // Scroll to form
                        const formSection = document.getElementById('booking-form-section');
                        if (formSection) {
                            formSection.scrollIntoView({ behavior: 'smooth' });
                            showNotification(`Selected ${dateStr} for your event!`, 'success');
                        }
                    } else {
                        // Redirect to contact page with date parameter
                        window.location.href = `contact.html?date=${dateStr}`;
                    }
                });
            } else {
                cell.style.cursor = 'not-allowed';
            }
            
            calendarContainer.appendChild(cell);
        }
    }

    // 4. Booking Form Redirect handling
    // If we loaded the contact page directly and passed a date param
    const urlParams = new URLSearchParams(window.location.search);
    const dateParam = urlParams.get('date');
    const formDateInput = document.getElementById('event-date');
    if (formDateInput && dateParam) {
        formDateInput.value = dateParam;
        showNotification(`Pre-selected date: ${dateParam}`, 'success');
    }

    // 5. Inquiry Form Submit Handling (AJAX API call)
    const bookingForm = document.querySelector('.booking-form');
    if (bookingForm) {
        bookingForm.addEventListener('submit', async function (event) {
            event.preventDefault();
            
            const name = document.getElementById('name').value.trim();
            const email = document.getElementById('email').value.trim();
            const phone = document.getElementById('phone').value.trim();
            const date = document.getElementById('event-date').value;
            const type = document.getElementById('event-type').value;
            const guests = document.getElementById('guest-count').value;
            const ac = document.getElementById('ac-option').value;
            const notes = document.getElementById('notes').value.trim();
            
            // Client-side validations
            if (name.length < 2) {
                showNotification("Name must be at least 2 characters.", "error");
                return;
            }
            if (!/^\+?[0-9\s-]{10,15}$/.test(phone)) {
                showNotification("Please enter a valid 10-15 digit phone number.", "error");
                return;
            }
            if (!date) {
                showNotification("Please select a preferred event date.", "error");
                return;
            }
            
            const payload = {
                name: name,
                email: email,
                phone: phone,
                event_date: date,
                event_type: type,
                guest_count: parseInt(guests),
                ac_option: ac,
                notes: notes
            };
            
            try {
                const response = await fetch('/api/inquiries', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(payload)
                });
                
                const resJson = await response.json();
                
                if (response.ok && resJson.status === 'success') {
                    showNotification('Inquiry submitted! We have blocked the date as pending and will contact you shortly.', 'success');
                    bookingForm.reset();
                    
                    // Refresh calendar if present on page
                    if (calendarContainer && monthYearTitle) {
                        const curYear = currentDate.getFullYear();
                        const curMonth = currentDate.getMonth();
                        loadAndRenderCalendar(curYear, curMonth);
                    }
                } else {
                    showNotification(resJson.detail || 'Inquiry submission failed. Please try again.', 'error');
                }
            } catch (err) {
                console.error("Error submitting booking inquiry:", err);
                showNotification('Network error. Failed to submit booking inquiry.', 'error');
            }
        });
    }

    // 6. Gallery Lightbox Modal
    const galleryItems = document.querySelectorAll('.gallery-item');
    const lightbox = document.getElementById('lightbox');
    
    if (galleryItems.length > 0 && lightbox) {
        const lightboxImg = lightbox.querySelector('.lightbox-content');
        const lightboxCaption = lightbox.querySelector('.lightbox-caption');
        const lightboxClose = lightbox.querySelector('.lightbox-close');
        
        galleryItems.forEach(item => {
            item.addEventListener('click', function () {
                const img = item.querySelector('img');
                const captionText = item.querySelector('.gallery-info h3').textContent;
                
                if (img) {
                    lightboxImg.src = img.src;
                    lightboxCaption.textContent = captionText;
                    lightbox.style.display = 'flex';
                }
            });
        });
        
        lightboxClose.addEventListener('click', function () {
            lightbox.style.display = 'none';
        });
        
        // Close on clicking overlay
        lightbox.addEventListener('click', function (e) {
            if (e.target === lightbox) {
                lightbox.style.display = 'none';
            }
        });
    }

    // 7. Admin Dashboard Control Logic
    const inquiriesTableBody = document.getElementById('admin-inquiries-body');
    const adminStats = {
        total: document.getElementById('stat-total-inquiries'),
        approved: document.getElementById('stat-approved-bookings'),
        pending: document.getElementById('stat-pending-requests')
    };
    
    const blockDateForm = document.getElementById('block-date-form');
    
    if (inquiriesTableBody) {
        // Load Inquiries and stats
        loadAdminDashboard();
        
        if (blockDateForm) {
            blockDateForm.addEventListener('submit', async function (e) {
                e.preventDefault();
                const blockDate = document.getElementById('block-date').value;
                const blockStatus = document.getElementById('block-status').value;
                
                if (!blockDate) {
                    showNotification('Please select a date to override.', 'error');
                    return;
                }
                
                try {
                    const response = await fetch('/api/admin/bookings/block', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify({ date: blockDate, status: blockStatus })
                    });
                    
                    const resJson = await response.json();
                    
                    if (response.ok && resJson.status === 'success') {
                        showNotification(`Date ${blockDate} set to ${blockStatus}!`, 'success');
                        blockDateForm.reset();
                        loadAdminDashboard(); // Reload data
                    } else {
                        showNotification(resJson.detail || 'Failed to update date status.', 'error');
                    }
                } catch (err) {
                    console.error("Error setting block slot:", err);
                    showNotification('Failed to connect to backend api.', 'error');
                }
            });
        }
    }
    
    async function loadAdminDashboard() {
        try {
            const response = await fetch('/api/admin/inquiries');
            if (!response.ok) {
                throw new Error("Failed to fetch inquiries");
            }
            
            const resJson = await response.json();
            const inquiries = resJson.data || [];
            
            // Calculate Stats
            let total = inquiries.length;
            let approved = inquiries.filter(i => i.status === 'approved').length;
            let pending = inquiries.filter(i => i.status === 'pending').length;
            
            if (adminStats.total) adminStats.total.textContent = total;
            if (adminStats.approved) adminStats.approved.textContent = approved;
            if (adminStats.pending) adminStats.pending.textContent = pending;
            
            // Render Table
            inquiriesTableBody.innerHTML = '';
            
            if (inquiries.length === 0) {
                const tr = document.createElement('tr');
                tr.innerHTML = `<td colspan="8" style="text-align: center; color: var(--color-text-muted);">No inquiries found.</td>`;
                inquiriesTableBody.appendChild(tr);
                return;
            }
            
            inquiries.forEach(inq => {
                const tr = document.createElement('tr');
                
                // Format event date
                const formattedDate = new Date(inq.event_date).toLocaleDateString('en-IN', { year: 'numeric', month: 'short', day: 'numeric' });
                const submittedDate = new Date(inq.created_at).toLocaleDateString('en-IN', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' });
                
                tr.innerHTML = `
                    <td><strong>${inq.name}</strong><br><span style="font-size:0.8em; color:var(--color-text-muted)">${submittedDate}</span></td>
                    <td><a href="tel:${inq.phone}">${inq.phone}</a><br><a href="mailto:${inq.email}" style="font-size:0.8em">${inq.email}</a></td>
                    <td><strong>${formattedDate}</strong></td>
                    <td style="text-transform: capitalize;">${inq.event_type}</td>
                    <td>${inq.guest_count}</td>
                    <td><span class="badge ${inq.ac_option}">${inq.ac_option.toUpperCase()}</span></td>
                    <td><span class="badge ${inq.status}">${inq.status}</span></td>
                    <td class="admin-actions">
                        ${inq.status === 'pending' ? `
                            <button class="btn-admin btn-approve" data-id="${inq.id}">Approve</button>
                            <button class="btn-admin btn-decline" data-id="${inq.id}">Decline</button>
                        ` : ''}
                        ${inq.status !== 'archived' ? `
                            <button class="btn-admin btn-archive" data-id="${inq.id}">Archive</button>
                        ` : '<span style="color:var(--color-text-muted)">No actions</span>'}
                    </td>
                `;
                
                // Add event listeners to the buttons
                const approveBtn = tr.querySelector('.btn-approve');
                const declineBtn = tr.querySelector('.btn-decline');
                const archiveBtn = tr.querySelector('.btn-archive');
                
                if (approveBtn) {
                    approveBtn.addEventListener('click', () => handleInquiryAction(inq.id, 'approved'));
                }
                if (declineBtn) {
                    declineBtn.addEventListener('click', () => handleInquiryAction(inq.id, 'declined'));
                }
                if (archiveBtn) {
                    archiveBtn.addEventListener('click', () => handleInquiryAction(inq.id, 'archived'));
                }
                
                inquiriesTableBody.appendChild(tr);
            });
            
        } catch (err) {
            console.error("Error loading dashboard data:", err);
            showNotification('Failed to load dashboard inquiries.', 'error');
        }
    }
    
    async function handleInquiryAction(id, newStatus) {
        try {
            const response = await fetch(`/api/admin/inquiries/${id}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ status: newStatus })
            });
            
            const resJson = await response.json();
            
            if (response.ok && resJson.status === 'success') {
                showNotification(`Inquiry status updated to ${newStatus}!`, 'success');
                loadAdminDashboard(); // Refresh table and stats
            } else {
                showNotification(resJson.detail || 'Action failed.', 'error');
            }
        } catch (err) {
            console.error("Error executing inquiry action:", err);
            showNotification('Network connection error.', 'error');
        }
    }
});