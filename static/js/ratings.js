let icons = document.querySelectorAll('#ratings svg');
let rating_input = document.querySelector('#rating_input');
let rating_form_div = document.querySelector('#rating_form_div');

function update_ratings(new_rating){
    new_rating = Number(new_rating);
    let icon_index = new_rating - 1;
    icons.forEach((icon,i) => {
        if (i <= icon_index) {
            // Brighten prior icons
            icon.classList.add('active');
        } else {
            // Dim remaining icons
            icon.classList.remove('active');
        }
        icon.setAttribute('aria-checked', i === icon_index ? 'true' : 'false');
        icon.setAttribute('tabindex', i === icon_index ? '0' : '-1');
    });
    // update input
    rating_input.value = new_rating;
    // unhide rating form
    rating_form_div.classList.remove('opacity-0');
}

function handleRatingKeydown(event, icon){
    const current = Number(icon.dataset.rating);
    if (event.key === 'Enter' || event.key === ' ') {
        event.preventDefault();
        update_ratings(current);
        return;
    }
    let next = null;
    if (event.key === 'ArrowRight' || event.key === 'ArrowUp') {
        next = Math.min(current + 1, icons.length);
    } else if (event.key === 'ArrowLeft' || event.key === 'ArrowDown') {
        next = Math.max(current - 1, 1);
    }
    if (next !== null) {
        event.preventDefault();
        update_ratings(next);
        icons[next - 1].focus();
    }
}
function hover_prior_ratings(new_rating){
    // Grab the gear icon that was last hovered
    let icon_index = new_rating - 1;
    // Slightly illuminate all prior icons
    icons.forEach((icon,i) => { 
        if (i <= icon_index) {
            icon.classList.add('hovered');
        }
            
    });
}
function unhover_prior_ratings(){
    hovered_icons =  document.querySelectorAll("svg.rating-icon.hovered");
    if (hovered_icons.length > 0)
        hovered_icons.forEach((hovered_icon)=>{hovered_icon.classList.remove('hovered')});
}
