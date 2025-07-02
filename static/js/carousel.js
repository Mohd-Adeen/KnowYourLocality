document.addEventListener('DOMContentLoaded', function() {
    const newsCarousel = document.querySelector('.news-carousel');
    if (newsCarousel) {
        // Pause animation on hover
        newsCarousel.addEventListener('mouseenter', function() {
            const track = this.querySelector('.news-track');
            track.style.animationPlayState = 'paused';
        });
        
        newsCarousel.addEventListener('mouseleave', function() {
            const track = this.querySelector('.news-track');
            track.style.animationPlayState = 'running';
        });
        
        // Clone news items for infinite loop
        const track = newsCarousel.querySelector('.news-track');
        const items = track.querySelectorAll('.news-item');
        
        items.forEach(item => {
            const clone = item.cloneNode(true);
            track.appendChild(clone);
        });
    }
});