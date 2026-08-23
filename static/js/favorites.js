function toggleFavorite(propertyId, btnElement) {
    fetch('/toggle-favorite', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ property_id: propertyId })
    })
    .then(response => {
        if (response.status === 401) {
            window.location.href = '/signin';
            return;
        }
        return response.json();
    })
    .then(data => {
        if (data && data.status === 'added') {
            btnElement.classList.add('active');
            alert('Add it to favorites!!');
        } else if (data && data.status === 'removed') {
            btnElement.classList.remove('active');
            alert('Delete from favorites!!');
        }
    })
    .catch(error => console.error('Error:', error));
}
