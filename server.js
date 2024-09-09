import express from 'express';
import fetch from 'node-fetch';
import { v4 as uuidv4 } from 'uuid';
import FormData from 'form-data';
import axios from 'axios';
import fs from 'fs';
import csv from 'csv-parser';
import _ from 'lodash';
import cloudscraper from 'cloudscraper';

import { CookieJar } from 'tough-cookie';
import { wrapper } from 'axios-cookiejar-support';

const jar = new CookieJar();
const client = wrapper(axios.create({ jar }));

const app = express();

const PORT = 8001;

const UPLOAD_API_TOKEN = "b30dfad361f96ae4044f54b45be9e23df73926d9f3387ff34063dc27bfee8441b91598fd8a30811c7c0f6c468b9215de5e0ef242fa48e85341691b39b21f554c9bad63d9575f0796153dd5d210fdfc948e9516eb3e11c1b735517ca68e60e5a2a433b1a72a84e27dbf423e29ede2875fc7e1fdf4da0078d34e508487ce43ca0f";

const uploadImageByUrl = async (url) => {
    try {
        console.log("url:  ", url);
        const response = await axios.get(url, {
            responseType: 'arraybuffer',
            headers: {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Referer': 'https://dev-api.gunsnation.com', // Replace with the referer if needed
                'Origin': 'https://dev-api.gunsnation.com', // Replace with the origin if needed
                'connection': 'keep-alive',
                'server': 'cloudflare',
                'cf-ray': '8ab7ffee5a649db5-DME'
            }
        });        
        const buffer = Buffer.from(response.data, 'binary');

        const contentType = response.headers.get('content-type');
        if (!contentType) {
            throw new Error(`Missing content type for image: ${imageResponse.url}`);
        }

        const extension = contentType.split('/')[1];
        if (!extension) {
            throw new Error(`Invalid content type for image: ${contentType}`);
        }
        
        const form = new FormData();
        const filename = `${uuidv4()}.${extension}`;

        console.log('extension:  ', extension, url);
        
        form.append('files', buffer, filename);
        
        const uploadResponse = await fetch('https://dev-api.gunsnation.com/api/upload', {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${UPLOAD_API_TOKEN}`,
                ...form.getHeaders()
            },
            body: form,
        });
    
        if (!uploadResponse.ok) {
            throw new Error(`Upload error: ${uploadResponse.statusText}`);
        }
        
        const images = await uploadResponse.json();
        if (!images[0]?.id) {
            throw new Error("Upload error, can't find result");
        }

        return images[0].id;

    } catch (error) {
        console.log('error:  ', error.message)
        console.log('Image uploading error =====================>');
        return false;
    }
}


const uploadProduct = async (product) => {
    const images = [];
    if (product.images) {
        const imageUrls = product.images.split(' ');
        if (imageUrls.length) {
            for (let i = 0; i < imageUrls.length; i++) {
                const response = await uploadImageByUrl(imageUrls[i].trim());
                if (response != false) images.push(response);
            }
        }
    }

    console.log('imageId ==> ', images)

    let capacity = {magazine: 0, chamber: 0}
    if (product.capacity) {
        const num = parseInt(product.capacity, 10);
        capacity = {magazine: num, chamber: 0}
    }

    let brand = null;
    if (product.brand) brand = { "name": product.brand }

    let upc = product.upc;
    if (upc && !isNaN(upc) && upc.includes('E')) {
        upc = Number(upc).toFixed(0);
    }

    let weight = product.weight ? parseFloat(product.weight) : 0;
    let barrel_length = product.barrel_length ? parseFloat(product.barrel_length) : 0;
    let overall_length = product.overall_length ? parseFloat(product.overall_length) : 0;
    if (weight == NaN || weight == undefined) weight = 0;
    if (barrel_length == NaN || barrel_length == undefined) barrel_length = 0;
    if (overall_length == NaN || overall_length == undefined) overall_length = 0;

    const data = {
        "data": {
            "category": product.category ? product.category : "",
            "upc": upc ? upc : "",
            "name": product.name ? product.name : "",
            "model": product.model ? product.model : "",
            "caliber": product.caliber ? product.caliber : "",
            "weight": weight,
            "barrel_length": barrel_length,
            "overall_length": overall_length,
            "capacity": capacity,
            "action": product.action ? product.action : "",
            "material": product.material ? product.material : "",
            "finish": product.finish ? product.finish : "",
            "sight_type": product.sight_type ? product.sight_type : "",
            "safety_features": product.safety_features ? product.safety_features : "",
            "product_description": product.product_description ? product.product_description : "",
            "color": product.color ? product.color : "",
            "gauge": product.gauge ? product.gauge : "",
            "frame_size": product.frame_size ? product.frame_size : "",
            "stock_material": product.stock_material ? product.stock_material : "",
            "stock_type": product.stock_type ? product.stock_type : "",
            "magazines_included": product.magazines_included ? product.magazines_included : "",
            "raw_data": product.raw_data ? product.raw_data : "",
            "brand": brand,
            "state_compliance": null,
            "images": {
                "ids": images,
            },
        }
    };

    console.log('data ==> ', data);


    try {
        await axios.post('https://dev-api.gunsnation.com/api/firearms/', data, {
            headers: {
                'Authorization': `Bearer ${UPLOAD_API_TOKEN}`,
                'Content-Type': 'application/json' // Set the content type if needed
            }
        })
    } catch (error) {
        console.error('An product uploading error occurred:', error.message);
    }
    
}



let data = [];
fs.createReadStream('./result/brownells_final.csv')
    .pipe(csv())
    .on('data', async (row) => {
        data.push(row);
        console.log('111111111111111111111111')
    })
    .on('end', async () => {
        // for (let i = 0; i < data.length; i++) {
        //     await uploadProduct(data[i])
        // }

        const batches = _.chunk(data.slice(0), 100);

        for (const batch of batches) {
            await Promise.all(batch.map(async (item) => {
                if (item) await uploadProduct(item);
            }));
        }

        console.log('CSV file successfully processed');
    });


app.listen(PORT, function() {
    console.log('Express server listening on port ', PORT); // eslint-disable-line
});