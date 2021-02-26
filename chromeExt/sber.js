let inputBox = document.querySelector('#searchInput')
inputBox.value = '32109992756'
let searchBtn = document.querySelector('.mainSearchBar-find')
searchBtn.click()

let viewAnchor = document.querySelector('a#STRView')
let iterations = 0
viewAnchor.click()

setTimeout(() => {
    // iterations += 1
 }, 1000)
window.close()

// while (iterations < 3) {
//     viewAnchor.click();
// }
