const fs = require('fs')

const { resolve } = require("node:path")
const { argv, cwd } = require("node:process")

const relativePathIN = argv[2]
const inFile = resolve(cwd(), relativePathIN)

const relativePathOUT = argv[3]
const outFile = resolve(cwd(), relativePathOUT)

const geoJSON = {
//  type: 'FeatureCollection',
  features: [],
}

fs.readFile(inFile, 'utf8', (err, data) => {
  const fences = data.match(/\[([^\]]+)\]([^\[]*)/g)
  fences.forEach(fence => {
    const geoFence = {
      name: '',
      path: [[]]
    }
    geoFence.name = fence.match(/\[([^\]]+)\]/)[1]
    geoFence.path[0] = fence.match(/[0-9\-\.]+,\s*[0-9\-\.]+/g).map(point => [parseFloat(point.split(',')[0]), parseFloat(point.split(',')[1])])
    geoFence.path[0].push(geoFence.path[0][0])

    geoJSON.features.push(geoFence)
  })

  fs.writeFile(outFile, JSON.stringify(geoJSON, null, 4), 'utf8', () => { })
})
