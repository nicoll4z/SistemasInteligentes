// Function to retrieve the user's name and profile picture.
$(document).ready(function() {
    $.ajax({
        url: 'user_informations',
        type: 'GET',
        dataType: 'json',
        success: function(response) {
            var username = response.username;
            var user_picture = response.user_picture;
            var img_tag = document.getElementById('user_picture')
            var username_tag = document.getElementById('username')

            img_tag.src = user_picture
            username_tag.innerHTML = username
        },
        error: function() {
            alert('Error when retrieving user information')
        }
    });
});


// Function to show the logout option.
const button = document.getElementById('user');

button.addEventListener('click', function(){
    let log_out = document.querySelector('.log_out');

    if (log_out.style.display == 'block') {
        log_out.style.display = 'none';
    }
    else {
        log_out.style.display = 'block';
    }
});


// mobile menu functions 
function mobile_icon(menu) {
    menu.classList.toggle("change");
}

const menu_icon = document.querySelector('.menu-mobile-icon');
menu_icon.addEventListener('click', function() {
    const menu = document.querySelector('.pages');
    if (menu.classList.contains('menu_open')) {
        menu.classList.remove('menu_open');
    }
    else {
        menu.classList.add('menu_open');
    }
});

// Function to get new songs recommendations without needing to refresh the page
$(document).ready(function () {
    $("#newPlaylist").click(function() {
        // AJAX request to get a new playlist
        $.ajax({
            url: '/get_new_playlist',
            type: 'GET',
            dataType: 'json',
            success: function(response) {
                var playlist_id = response.playlist_id;
                var iframe = document.getElementById('songsFrame');
                iframe.src = 'https://open.spotify.com/embed/playlist/' + playlist_id + '?utm_source=generator&theme=0';
            },
            error: function() {
                alert("Error when retrieving new playlist");
            }
        });
    });
});