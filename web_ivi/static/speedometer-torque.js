const speedTorqueRelation = [{
    speed: 0,
    torque: "D1"
}, {
    speed: 20,
    torque: "D2"
}, {
    speed: 30,
    torque: "D3"
}, {
    speed: 40,
    torque: "D4"
}, {
    speed: 70,
    torque: "D5"
}, {
    speed: 80,
    torque: "D6"
}, {
    speed: 100,
    torque: "D7"
}];


/* update the speed-value by a number */
function updateSpeedValue(speed, accelerationFactor) {
    // update the speed value fluently by a number
    let speedValue = document.getElementById("speed-value");
    let torqueValue = document.getElementById("torque-value");
    let currentSpeed = parseInt(speedValue.textContent);
    let increment = 1;
    let speedDiff = speed - currentSpeed;
    let speedStep = Math.sign(speedDiff) * increment;
    let intervalTime = 100 / accelerationFactor; // calculate the interval time based on the acceleration factor
    let speedInterval = setInterval(() => {
        currentSpeed += speedStep;
        // check if the currentSpeed is greater or equal the last speed in the speedTorqueRelation
        if (speedTorqueRelation.length > 0 && currentSpeed >= speedTorqueRelation[speedTorqueRelation.length - 1].speed) {
            torqueValue.textContent = speedTorqueRelation[speedTorqueRelation.length - 1].torque;
        } else {
            let torque_out = speedTorqueRelation.find((element) => {
                return currentSpeed <= element.speed;
            });
    
            if (torque_out) {
                torqueValue.textContent = torque_out.torque;
            }
        }

        speedValue.textContent = currentSpeed;
        if (currentSpeed == speed) {
            clearInterval(speedInterval);
        }
    }, intervalTime);
}