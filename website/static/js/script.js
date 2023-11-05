// init Isotope
var $grid = $('.collection-list').isotope({

});
// filter items on button click
$('.filter-button-group').on( 'click', 'button', function() {
  var filterValue = $(this).attr('data-filter');
  resetFilterBtns();
  $(this).addClass('active-filter-btn');
  $grid.isotope({ filter: filterValue });
});

var filterBtns = $('.filter-button-group').find('button');
function resetFilterBtns(){
  filterBtns.each(function(){
    $(this).removeClass('active-filter-btn');
  });
}

document.addEventListener("DOMContentLoaded", function () {
  const flashContainer = document.getElementById("flash-container");
  const flashMessage = document.getElementById("flash-message");
  const closeFlashButton = document.getElementById("close-flash");
  
  flashContainer.style.display = "block";
  setTimeout(function () {
      flashContainer.style.display = "none";
  }, 7000);
  
  closeFlashButton.addEventListener("click", function () {
      flashContainer.style.display = "none";
  });
});
