// const keywords = ['авсе', 'агс', 'пожар']
const keywords = ['авсе']
let inputBox = document.querySelector('#filterField-0-input')
let searchBtn = document.querySelector('#applyFilterButton')
let viewAnchor = document.querySelector('a#STRView')

let iterations = 0
while (iterations < 3) {
    viewAnchor.click();
    setTimeout(() => {
        iterations += 1
     }, 1000)
}

// for (let keyword of keywords) {
//     let inputBox = document.querySelector('#filterField-0-input')
//     let searchBtn = document.querySelector('#applyFilterButton')
//     inputBox.value = keyword;
//     searchBtn.click()
//     setTimeout(() => {
//         elements = document.getElementsByClassName('card p-grid')
//         for (let el of elements) {
//             number = el.getElementByID('tradeNumber')
//             res.push(number)
//         }
//         console.log(res.length)
//     }, 100)
    
// }
