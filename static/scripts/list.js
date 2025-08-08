function onCategoryChange(select) {
    const category = select.value;
    if (category === 'none') {
        window.location.href = `/list/1`;
    } else {
        window.location.href = `/list/1/${category}`;
    }
}