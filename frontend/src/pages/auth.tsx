import Cookies from 'universal-cookie';
const cookies = new Cookies();

const BACKEND_URL = 'http://localhost:8000';

function getToken() {
    return cookies.get("csrftoken");
}

async function isResponseOk(response: Response) {
    if (response.ok) {
        // response.ok is true for 200–299
        return await response.json();
    } else {
        const errorData = await response.json(); // wait for the body to be parsed
        console.log(errorData);
        throw new Error(errorData.msg || 'Unknown error');
    }
}

export {BACKEND_URL, getToken, isResponseOk}