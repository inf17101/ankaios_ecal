var sideseeings = [];
let currentIndex = 0;
let lock = false;
let vehicle_within_city = false;

const createElement = (tag, text, className) => {
    const element = document.createElement(tag);
    if (className) {
        element.className = className;
    }
    if (text) {
        element.textContent = text;
    }
    return element;
};

const createLinkElement = (url, text, className) => {
    const element = document.createElement('a');
    if (className) {
        element.className = className;
    }
    element.href = url;
    element.target = '_blank';
    element.textContent = text;
    return element;
};

// Function to update the sideseeing info content
function updateSightseeingInfo() {
    if (lock) {
        return;  // Skip update if locked
    }

    let infoScreenMainDiv = document.getElementById('info-screen');
    let siteInfoDiv = document.getElementsByClassName('site-info')[0];

    // check if siteInfoDiv is not null and if siteInfoDiv is a child of infoScreenMainDiv then remove it
    if (infoScreenMainDiv == null) {
        console.log("Cannot update sightseeing info: infoScreenMainDiv is null");
        return;
    }

    // delete all the current content inside the sightseeing info div
    if (siteInfoDiv != null) {
        infoScreenMainDiv.removeChild(siteInfoDiv);
    }

    // set speed limit based on vehicle_within_city
    if (vehicle_within_city) {
        updateSpeedValue(50, 2);
    } else {
        updateSpeedValue(100, 2);
    }

    if (sideseeings.length == 0) {
        console.log("sideseeings list is empty. Skipping to display element");
        return;
    }

    const siteInfo = createElement('div', null, 'site-info');

    let sightseeingData = sideseeings[currentIndex];
    
    if (sightseeingData.name == null) {
        console.log("sightseeingData.name is null. Skipping to display element");
        return;
    }

    console.log(sightseeingData.name);
    const name = createElement('h2', sightseeingData.name);
    siteInfo.appendChild(name);

    if (sightseeingData.type) {
        const type = createElement('p', `Type: ${sightseeingData.type}`);
        siteInfo.appendChild(type);
    }

    if (sightseeingData.fee) {
        const fee = createElement('p', `Entrance Fee: ${sightseeingData.fee}`);
        siteInfo.appendChild(fee);
    }
    
    if (sightseeingData.website) {
        const website = createElement('p');
        website.innerHTML = `Website: `;
        website.appendChild(createLinkElement(sightseeingData.website, 'Visit Website'));
        siteInfo.appendChild(website);
    }

    if (sightseeingData.openingHours) {
        const openingHours = createElement('p', `Opening Hours: ${sightseeingData.openingHours}`);
        siteInfo.appendChild(openingHours);
    }
    
    if (sightseeingData.addrStreet && sightseeingData.addrHousenumber && sightseeingData.addrPostcode && sightseeingData.addrCity) {

        const address = createElement('p', `Address: ${sightseeingData.addrStreet} ${sightseeingData.addrHousenumber}, ${sightseeingData.addrPostcode} ${sightseeingData.addrCity}`);
        siteInfo.appendChild(address);
    } else if (sightseeingData.addrStreet && sightseeingData.addrHousenumber) {
        const address = createElement('p', `Address: ${sightseeingData.addrStreet} ${sightseeingData.addrHousenumber}`);
        siteInfo.appendChild(address);
    } else if (sightseeingData.addrStreet) {
        const address = createElement('p', `Address: ${sightseeingData.addrStreet}`);
        siteInfo.appendChild(address);
    }

    infoScreenMainDiv.appendChild(siteInfo);
    currentIndex = (currentIndex + 1) % sideseeings.length;
}

// read from server-side event /sideseeings
const eventSource = new EventSource("/sideseeings");

eventSource.onopen = function (_event) {
    console.log("Connection to /sideseeings opened");
}

// add event listener for the event
eventSource.addEventListener("sideseeings", function (event) {
    let raw_data = event.data;
    let attraction_json = JSON.parse(raw_data);

    if (attraction_json.addrStreet == null) {
        console.log("skipping sideseeing without address.");
        return;
    }

    console.log(attraction_json);
    lock = true;  // Lock the list
    sideseeings.push(attraction_json);
    currentIndex = 0;  // Reset current index to start from the beginning
    lock = false;  // Unlock the list
});

eventSource.addEventListener("vehicle_within_city", function (event) {
    let raw_data = event.data;
    let payload = JSON.parse(raw_data);

    if (payload.is_within_city == null) {
        console.log("invalid payload: event type 'vehicle_within_city' has no key 'is_within_city'.");
        return;
    }

    console.log("Received vehicle_within_city: ", payload.is_within_city);
    lock = true; // Lock
    // check if vehicle is outside city and clear the sideseeings to not display them anymore
    vehicle_within_city = payload.is_within_city;

    if (!vehicle_within_city) {
        sideseeings = []; // clear sideseeings list
        currentIndex = 0;
    }
    lock = false; // Unlock
});

// close the connection on error
eventSource.onerror = function (event) {
    console.log("Error: " + event);
    eventSource.close();
}

// Call the updateSightseeingInfo function every 3 seconds (3000 milliseconds)
setInterval(updateSightseeingInfo, 3000);