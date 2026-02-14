document.addEventListener("DOMContentLoaded", () => {

  /* ================================
     PRODUCT ROTATOR (WAVE BAR)
  ================================= */
/*
  const slides = document.querySelectorAll(".wave-slide");
  const bgLayers = document.querySelectorAll(".wave-bg");

  if (slides.length && bgLayers.length >= 2) {

    let current = 0;
    let bgIndex = 0;

    // Preload images
    slides.forEach(slide => {
      const img = slide.querySelector("img");
      const preload = new Image();
      preload.src = img.src;
    });

    // First slide
    slides[0].classList.add("active");
    bgLayers[0].style.backgroundImage =
      `url(${slides[0].querySelector("img").src})`;
    bgLayers[0].classList.add("active");

    setInterval(() => {

      slides[current].classList.remove("active");

      current = (current + 1) % slides.length;

      slides[current].classList.add("active");

      bgIndex = (bgIndex + 1) % 2;

      const nextBg = bgLayers[bgIndex];
      const prevBg = bgLayers[(bgIndex + 1) % 2];

      nextBg.style.backgroundImage =
        `url(${slides[current].querySelector("img").src})`;

      nextBg.classList.add("active");
      prevBg.classList.remove("active");

    }, 1200);

  }

*/
  /* ================================
     WISHLIST TOGGLE
  ================================= */

  document.querySelectorAll(".wishlist").forEach(btn => {

    btn.addEventListener("click", () => {
      btn.classList.toggle("active");
    });

  });


  /* ================================
     ADD TO CART EFFECT
  ================================= */

  document.querySelectorAll(".add-cart-btn").forEach(btn => {

    btn.addEventListener("click", () => {

      const id = btn.dataset.id;

      fetch(`/add-to-cart/${id}`)
        .then(res => res.json())
        .then(data => {

          if (data.status === "out_of_stock") {
            btn.innerHTML = "Out of Stock";
            btn.disabled = true;
            btn.classList.add("btn-secondary");
            return;
          }

          btn.innerHTML = "✔ Added";
          btn.disabled = true;

          const cartCount = document.getElementById("cartCount");
          if (cartCount) {
            cartCount.innerText = data.count;
          }

          setTimeout(() => {
            btn.innerHTML = "Add To Cart";
            btn.disabled = false;
          }, 1500);

        });


    });

  });


  /* ================================
     REVIEW COUNTER ANIMATION
  ================================= */

  const counter = document.getElementById("reviewCounter");

  if (counter) {

    let count = 0;
    const target = 611;

    const counterInterval = setInterval(() => {

      count += 6;

      if (count >= target) {
        count = target;
        clearInterval(counterInterval);
      }

      counter.innerText = count;

    }, 15);

  }


  /* ================================
     FADE IN REVIEW SECTION
  ================================= */

  const ratingSection = document.getElementById("ratingSection");

  if (ratingSection) {

    ratingSection.classList.add("hidden");

    window.addEventListener("scroll", () => {

      const top = ratingSection.getBoundingClientRect().top;

      if (top < window.innerHeight - 100) {
        ratingSection.classList.add("visible");
      }

    });

  }

});
// Instagram infinite loop duplication

const instaTrack = document.getElementById("instaTrack");

if(instaTrack){
  instaTrack.innerHTML += instaTrack.innerHTML;
}

/* Mobile menu */

const hamburger = document.getElementById("hamburger");
const navMenu = document.getElementById("navMenu");

if (hamburger && navMenu) {
  hamburger.addEventListener("click", () => {
    navMenu.classList.toggle("show");
  });
}


/* Shadow on scroll */

window.addEventListener("scroll", () => {

  const navbar = document.querySelector(".main-navbar");

  if (window.scrollY > 30) {
    navbar.classList.add("scrolled");
  } else {
    navbar.classList.remove("scrolled");
  }

});

/* Cart count auto update */

fetch("/cart-count")
.then(res => res.json())
.then(data => {
  const cartCount = document.getElementById("cartCount");
  if (cartCount) {
    cartCount.innerText = data.count;
  }

});

window.addEventListener("load", () => {
  document.getElementById("pageLoader").style.display = "none";
});

const reveals = document.querySelectorAll(".reveal");

window.addEventListener("scroll", () => {

  reveals.forEach(el => {

    const top = el.getBoundingClientRect().top;
    const windowHeight = window.innerHeight;

    if (top < windowHeight - 100) {
      el.classList.add("active");
    }

  });

});

const backTop = document.getElementById("backTop");

if (backTop) {
  window.addEventListener("scroll", () => {
    if (window.scrollY > 400) {
      backTop.style.display = "block";
    } else {
      backTop.style.display = "none";
    }
  });

  backTop.addEventListener("click", () => {
    window.scrollTo({ top: 0, behavior: "smooth" });
  });
}

function openInstagram(el) {
  const url = el.getAttribute("data-url");
  if (url) {
    window.open(url, "_blank");
  }
}

document.querySelectorAll(".increase").forEach(btn => {
    btn.addEventListener("click", function () {
        const id = this.dataset.id;
        window.location.href = "/cart/increase/" + id;
    });
});

document.querySelectorAll(".decrease").forEach(btn => {
    btn.addEventListener("click", function () {
        const id = this.dataset.id;
        window.location.href = "/cart/decrease/" + id;
    });
});


// Star rating input
document.addEventListener("DOMContentLoaded", function () {
    const stars = document.querySelectorAll(".star");
    const ratingInput = document.getElementById("rating");

    if (stars.length > 0 && ratingInput) {
        stars.forEach(star => {
            star.addEventListener("click", function () {
                const value = this.getAttribute("data-value");
                ratingInput.value = value;

                stars.forEach(s => s.classList.remove("active"));

                for (let i = 0; i < value; i++) {
                    stars[i].classList.add("active");
                }
            });
        });
    }
});




