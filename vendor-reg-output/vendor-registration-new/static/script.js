const steps = document.querySelectorAll(".step");
const nextBtns = document.querySelectorAll(".next");
const prevBtns = document.querySelectorAll(".prev");

let currentStep = 0;

function showStep(step){
    steps.forEach((s,index)=>{
        s.classList.remove("active");
        if(index === step){
            s.classList.add("active");
        }
    });
}

function validateStep(step){

    const inputs = steps[step].querySelectorAll("input, select");

    for(let input of inputs){
        if(!input.checkValidity()){
            input.reportValidity();
            return false;
        }
    }

    return true;
}

nextBtns.forEach(btn=>{
    btn.addEventListener("click", ()=>{

        if(validateStep(currentStep)){

            if(currentStep < steps.length - 1){
                currentStep++;
                showStep(currentStep);
            }

        }

    });
});

prevBtns.forEach(btn=>{
    btn.addEventListener("click", ()=>{

        if(currentStep > 0){
            currentStep--;
            showStep(currentStep);
        }


    });
});

showStep(currentStep);