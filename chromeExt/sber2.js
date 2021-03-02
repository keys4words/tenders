setTimeout(() => {
    console.log('3 seconds gone...')
}, 3000)

let chooseBtn = document.querySelector('#RegionidControl a')
chooseBtn.click()

setTimeout(() => {
    console.log('3 seconds gone...')
}, 1000)

document.elementFromPoint(967, 200).querySelector('a').click()

// const close = document.querySelector('.ui-icon.ui-icon-closethick')
// close.getBoundingClientRect()


// document.elementFromPoint(x, y).click();
// let inputName = document.querySelector('#tbName')
// inputName.value = 'Байконур'

// let searchBtn = document.querySelector('#btnSearch')
// searchBtn.click()

// let closePopupBtn = document.querySelector('.ui-dialog-titlebar-close.ui-corner-all')
// closePopupBtn.click()

