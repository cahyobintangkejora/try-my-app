$(() => {
    esc_close_modal();

    // adjust datatable every time admin-lte push menu change
    $(document).on('collapsed.lte.pushmenu shown.lte.pushmenu', function () {
        adjustDataTable();
    });
})

function removeFormAction() {
    /*
        Remove element when (current_user) user_roles don't have the specified roles on attr `acc-roles`
    */
    document.querySelectorAll('[acc-roles]').forEach(element => {
        const acc_roles = element.getAttribute('acc-roles').split(' ');

        if (!acc_roles.some(ar => user_roles.includes(ar))) {
            element.remove();
        }
    })
}

// not implement, khusus bmt
function disableFormAction() {
    return;
}

// fungsi untuk sanitasi text mencegah XSS
function sanitize(string_text) {
    return DOMPurify.sanitize(string_text).trim();
}

function decodeHtml(text) {
    /*
        Fungsi ini menghapus tag HTML, contoh :
            INPUT: decodeHtml("<script>alert('ok')</script>");
            OUTPUT: "alert('ok')"
        Juga unescape HTML, contoh:
            INPUT: decodeHtml("&lt;script&gt;alert(&#x27;ok&#x27;)&lt;/script&gt;");
            OUTPUT: "<script>alert('ok')</script>"
        Karena fungsi ini unescape HTML maka BERPOTENSI terjadi XSS, jadi gunakan dengan bijak!
     */
    const doc = new DOMParser().parseFromString(text, "text/html");
    return doc.documentElement.textContent;
}

function decodeHtmlObj(obj) {
    // NOTE: Ingat ini berpotensi terjadi XSS, gunakan dengan bijak!
    const copy_obj = JSON.parse(JSON.stringify(obj));
    for (const [k, v] of Object.entries(copy_obj)) {
        if (typeof (v) === 'string') {
            copy_obj[k] = v.decodeHtml();
        }
    }
    return copy_obj;
}

String.prototype.decodeHtml = function () {
    // NOTE: Ingat ini berpotensi terjadi XSS, gunakan dengan bijak!
    return decodeHtml(this);
}

String.prototype.sanitize = function () {
    const temp = sanitize(this);
    const escapeHtml = unsafe => {
        return unsafe
            .replaceAll('&', '&amp;')
            .replaceAll('<', '&lt;')
            .replaceAll('>', '&gt;')
            .replaceAll('"', '&quot;')
            .replaceAll("'", '&#039;');
    }
    return temp ? temp : escapeHtml(this);
}

/*
    Jika string berupa signed data maka bisa pakai fungsi ini untuk ektract payload / value-nya.
    Contoh:
        let kd_cabang = '"KZ01"$.$jt7uiNKe3inpnFK0JttdrpBxLYI';
        kd_cabang.extractPayload(); -> ouput: "KZ01"
*/
String.prototype.extractPayload = function () { return this.split('$.$')[0].replace(/\\"/g, '"').slice(1, -1); };

function ajaxErrorHandler(response) {
    /*
        di-python, sudah dibuat 3 jenis response ajax:
            - ajaxNormalError: untuk normal error, hanya tampil pesan error saja.
            - return validationError(: untuk error 400(Bad Request) karena form/args yg dikirm tidak valid, tampilkan seluruh list pesan error dlm bentuk stacking toastr.
            - ajaxRedirect: jika ingin return redirect namun dari request yg bentuknya XHR(ajax).
        fungsi in dibuat untuk handle semua jenis reseponse ajax diatas.
        NOTE: fungsi ditest dgn ajax jQuery, belum dicoba jika pakai ajax lain (fetch API, XHR, dll).
    */
    hideBaseLoading();
    r = response;

    if (response.readyState == 0) {
        // jika session habis/user belum login, maka readyState menjadi 0, sehingga kita info ke user untuk login ulang
        // TODO: bikin modal untuk user bisa login secara langsung dari modal, jadi use tetap bisa lanjut activity tanpa harus redirect ke login
        Swal.fire({
            icon: 'error',
            title: '<span class="text-red bg-yellow">VPN / App Mati!</span>',
            html: "<p>Coba cek VPN atau applikasinya udah jalan belum. Atau mungkin session-nya abis?</p>"
        })
    } else if (response.responseJSON) {
        /*
            reseponseJSON terdiri dari 2 attribute:
                - errorType: tipe dari ajax error, yaitu "ajaxNormalError", "validationError", "ajaxRedirect"
                - result: playload yg akan kita prosess:
                    - jika ajaxNormalError maka berisi pesan error untuk ditampilkan ke user.
                    - jika validationError maka berisi array of obj dari form/args yg error.
                    - jika ajaxRedirect maka berisi location, data, method untuk redirect.
        */
        const { errorType, result } = response.responseJSON;

        switch (errorType) {
            case 'ajaxNormalError':
                // ajaxNormalError resultnya cuma text/string error aja,
                // tampilkan pesan error ke user pakai swal
                messageAlert('e', result);
                break;
            case 'validationError':
                // validationError result-nya dlm bentuk array of obj: [{'key': 'umur', 'value': 100, 'message': 'umur tidak boleh >99'}, ...]
                // kita tampilkan semuanya ke user pakai stacking toastr.
                result.forEach(error => {
                    const message = `${error.key}: ${error.value} -> ${error.message}`;
                    toastr.error(message);
                })
                break;
            case 'ajaxRedirect':
                /*
                    ajaxRedirect resultnya berisi obj dgn 3 attribute:
                        - 'location': yaitu URL tujuan untuk 'redirect' dari current page.
                        - 'data': yaitu form/args yg akan dikirim ke url tujuan.
                        - 'method': GET, POST, etc.
                    NOTE: dev masih belum selesai, antrian..
                */
                const form = $(
                    `<form action="/error-page" method="POST"><input name='error_message' value="${res.error_message}"/><button type='submit'></form>`
                );
                $('body').append(form);
                form.trigger('submit');
                break;
            default:
                break;
        }
    } else {
        // semua ajaxError content-type-nya JSON. Jika responseJSON kosong, maka render sebagai html
        Swal.fire({
            icon: 'error',
            title: `<span class="text-red bg-yellow">${response.status} - ${response.statusText}</span>`,
            html: response.responseText
        })
    }
}

function messageAlert(status = 'e', message) {
    const statusIcon = (() => {
        switch (status.toLocaleLowerCase()) {
            case 's':
            case 'success':
                return 'success';
            case 'i':
            case 'info':
                return 'info';
            case 'w':
            case 'warning':
                return 'warning';
            case 'e':
            default:
                return 'error';
        }
    })();

    Swal.fire({
        icon: statusIcon,
        title: `<p style="text-align: left; margin: 10px 10px;">${message}</p>`,
        toast: true,
        position: 'top-end',
        showConfirmButton: false,
        timer: 3000,
        timerProgressBar: true,
        didOpen(toast) {
            toast.addEventListener('mouseenter', Swal.stopTimer)
            toast.addEventListener('mouseleave', Swal.resumeTimer)
        }
    })
}

function swalConfirm(swal_options) {
    return Swal.fire({
        title: 'Konfirmasi',
        html: "Apakah anda yakin?",
        icon: 'question',
        showCancelButton: true,
        confirmButtonColor: '#3085d6',
        cancelButtonColor: '#d33',
        confirmButtonText: 'Yakin',
        cancelButtonText: 'Batal',
        ...swal_options
    })
}

//hide and show loading

//fungsi untuk refresh dataTable
function refreshTable(idTable) {
    //hapus table row
    $(`#${idTable} > tbody > tr`).remove();
    //cari element pagination
    const obj = document.querySelector("ul.pagination");
    //sembunyikan elemen pagination jika ada (saja)
    obj ? obj.style.visibility = 'hidden' : '';
    //refresh tabel
    $('#' + idTable).DataTable().ajax.reload(null, false);
    // hideLoading();
}

//fungsi untuk adjust / merapikan tampilan dataTable
function adjustDataTable() {
    setTimeout(() => {
        $.fn.dataTable.tables({ visible: true, api: true }).columns.adjust();
    }, 300);
}

//fungsi listener form submit
$(function () {
    document.querySelectorAll("form").forEach(form => {
        //ketika submit form maka akan show loading dan element dinon-aktifkan sementara
        form.addEventListener('submit', obj => {
            showLoading();
        });
    });
})

//setelah render element selesai jalankan fungsi removeFormAction()
// $(() => {
//     removeFormAction();
//     disableFormAction();
// })



//fungsi ini dugunakan untuk auto focus pada saat user menambahkan data baru ke <table>
//tujuan di buat focus agar user tahu bahwa ia baru saja menambahkan data (row) baru
function scrollEndRow(id_tabel) {
    document.querySelector(`#${id_tabel}_wrapper .dataTables_scrollBody`).scrollBy({
        top: 10000,
        behavior: 'smooth'
    });
}

//fungsi untuk mengecek apakah value dari input text itu melebihi kotak input-nya?
//misal: ada input ukuran kecil 10px, tapi isi text-nya panjang sekali melebihi 10px,
//maka return fungsi ini jadi true
function isInputOverFlow(idElement) {
    input = document.getElementById(idElement);
    return input.scrollWidth > input.clientWidth;
}

//fungsi untuk show snackbar 
function showSnackbar(message = 'Hallo dunia', durasiDetik = 2) {
    // Get the snackbar DIV
    const x = document.getElementById("snackbar");
    x.innerText = message;

    // Add the "show" class to DIV
    x.className = "show";

    // After 3 seconds, remove the show class from DIV
    setTimeout(function () {
        x.className = x.className.replace("show", "");
    }, durasiDetik * 1000);
}

function esc_close_modal() {
    /*
        fungsi tekan esc untuk close modal lov atau modal action
        fungsi untuk menutup modal secara stack FILO (first in last out),
        misal ada modal A, dalam modal A panggil modal B (numpuk berarti),
        ketika pencet tombol ESC kita mau tutup modal paling atas yaitu B,
        pencet ESC lagi maka tutup modal A
    */
    const modal_stacks = [];
    const kecuali = modal_element => {
        // kecualikan modal yg memiliki class .esc-no-close dan
        const className = ['esc-no-close', 'bootbox'];
        if (className.some(className => modal_element.classList.contains(className))) return true;
    };

    (() => {
        $(document).on('keydown', key => {

            if (key.key !== 'Escape' || document.querySelector('.bootbox')) return;

            if (modal_stacks.length < 1) {
                document.querySelectorAll('.modal.show').forEach(e => {
                    if (kecuali(e)) return;
                    $(e).modal('hide');
                })
            }

            $('#' + modal_stacks.pop()).modal('hide');
        }).on('show.bs.modal', e => {
            if (kecuali(e.target)) return;

            try {
                modal_stacks.push(e.target.id);
            } catch (err) {
                // do nothing
            }
        }).on('hide.bs.modal', e => {
            try {
                if (kecuali(e.target)) return;

                const indexHapus = modal_stacks.indexOf(e.target.id);

                // ada bug nggak tau dari mana, dimana ketika kita buka 2 modal,
                // kemudian pencet ESC langsung, itu akan tutup modal index ke 0.
                // sehingga dibuatlah kondisi ini untuk mengatasi bug tersebut :)
                if (indexHapus == 0 && modal_stacks.length > 1) e.preventDefault();

                if (indexHapus >= 0) {
                    modal_stacks.splice(indexHapus, 1);
                }
            } catch (err) {
                // do nothing
            }
        })
    })();

}

function dt_server(id_tabel, ajax_options, dt_options) {
    // setup when ajax error (status code != 2xx)
    ajax_options = {
        ...{
            error: res => {
                $('#' + id_tabel).DataTable().destroy();
                $(`#${id_tabel} tbody`).append(`
                    <div class="card-404 center-error d-flex align-items-center m-auto">
                        <i class="fas fa-exclamation-circle mr-2 color-red- font-24"></i>
                        <p class="m-0">${res.status} - ${res.statusText}</p>
                    </div>
                `).css('position', 'relative');
                ajaxErrorHandler(res);
            }
        },
        ...ajax_options,
    };
    dt_options = {
        ...{
            scrollY: '30vh'
        },
        ...dt_options,
    };

    // reset && destroy table
    $('#' + id_tabel + ' tbody').html('');
    $('#' + id_tabel).DataTable().clear().destroy();

    // create data table
    $('#' + id_tabel).DataTable({
        responsive: true,
        fixedHeader: true,
        scrollX: true,
        lengthChange: false,
        pageLength: 10,
        processing: true,
        serverSide: true,
        ajax: ajax_options,
        searching: false,
        sort: false,
        ordering: false,
        order: [],
        orderable: false,
        info: false,
        language: {
            processing: `
                <img
                    src="/static/image/alfamart/alfamart_loading.gif"
                    alt="Loading.."
                    width="100%"
                    height="100%" style="opacity: .8; border-radius:100px;"
                >
            `,
            emptyTable: `
                <div class="card-404 d-flex align-items-center m-auto">
                    <i class="fas fa-exclamation-circle mr-2 color-red- font-24"></i>
                    <p class="m-0">Gagal Memuat Data!</p>
                </div>
            `,
            zeroRecords: "Data Kosong"
        },
        columnDefs: [],
        drawCallback: function (settings) {
            document.querySelector(`#${id_tabel} > tbody`).style.height = 'auto';
            removeFormAction();
        },
        preDrawCallback: function (settings) {
            document.querySelector(`#${id_tabel} > tbody`).style.height = '30vh';
        },
        paging: true,
        ...dt_options
    });

    // fix bug datatable.
    $('.sorting_asc').removeClass('sorting_asc');

    // attach error listener
    $.fn.dataTable.ext.errMode = 'none';
    $('#' + id_tabel).off('error.dt').on('error.dt', (e, settings, techNote, message) => {
        messageAlert('e', message.split('- ')[1]);
    });

    adjustDataTable();
}

//parameter p_search di-isi dengan letak kotak cari (left, center, right);
function dt_client(idTabel, dt_options) {
    try {
        $('#' + idTabel).DataTable().clear().destroy();
    } catch (e) {
        //do nothing
    }

    $('#' + idTabel).DataTable({
        info: false,
        pageLength: 10,
        paging: true,
        searching: true,
        processing: true,
        lengthChange: false,
        ordering: false,
        scrollY: '30vh',
        scrollX: true,
        ...dt_options
    });
    $('.sorting_asc').removeClass('sorting_asc');
    adjustDataTable();
}

//fungsi untuk memindahkan search dataTable
//param direction diisi dengan left / center / right
//sementara hanya dapat digunakan jika dataTable tidak ada property dom
function moveDTSearch(idTabel, direction) {
    direction = typeof (direction) != 'string' ? 'left' : direction;
    //get div search filter data tabl   e
    let searchDiv;
    try {
        searchDiv = document.getElementById(`${idTabel}_filter`).closest('div.row');
    } catch (TypeError) {
        messageAlert('W', "Gagal memindahkan search dataTable: Tabel tidak ditemukan!");
        // hideLoading();
    }
    //data table memiliki 2 div element (yg harusnya cuma 1), mungkin bug dataTable-nya
    //jadi jida ada 2 div kita hapus saja
    const bugDiv = searchDiv.children;
    if (bugDiv.length > 1) {
        bugDiv[0].remove();
    }
    //sesuaikan dengan direction (left, center, right)
    let v_class = 'row justify-content-center';
    if (direction.match('right')) {
        v_class = 'row justify-content-end mr-2';
    } else if (direction.match('left')) {
        v_class = 'row justify-content-start';
    }

    searchDiv.className = '';
    searchDiv.className = v_class;
}

//fungsi untuk hard reload data tabel
function hardReloadTable(idTabel, newData) {
    const dataTable = $('#' + idTabel).DataTable();
    dataTable.clear().draw();
    dataTable.rows.add(newData);
    dataTable.columns.adjust().draw();
}

function getInitials(fullName) {
    if (typeof (fullName) != 'string') return;

    // ambil nama depan kemduian jadikan tittle case,
    // ambil sisa namanya dijadikan inisial dan huruf besar
    // contoh "DANIEL HARLIANO SITORURS" -> ["DANIEL", "HARLIANO", "SITORUS"] -> ["Daniel", "H", "S"]
    const split_name = fullName.split(' ');
    const format_name = [];
    for (let i = 0; i < split_name.length; i++) {
        if (i == 0) {
            format_name.push(
                split_name[i][0].toUpperCase() + split_name[i].slice(1).toLowerCase()
            );
        } else {
            format_name.push(
                split_name[i][0].toUpperCase()
            );
        }
    }

    // build array jadi string nama
    // ["Daniel", "H", "S"] -> "Daniel H S"
    return format_name.join(" ")
}

function sendFormRequest(url = '#', method = 'GET', data) {
    /* 
        Fungsi untuk send HTTP request dengan bantuan element form.
        Cocok untuk kirim request ke controller yang return-nya file download.
        fungsi ini menerima param/argument:
            url: merupakan url controller, contoh:  "/downloadExcel".
            method: "GET", "POST", dll.
            data: data dalam bentuk json, contoh: {'nama': 'candra', 'nik': 'xxx'}
    */

    const form = document.createElement('form');
    form.method = method.toUpperCase();
    form.action = url;
    form.style.display = 'none';

    if (data) {
        for (const [k, v] of Object.entries(data)) {
            const input = document.createElement('input');
            input.name = k;
            input.value = v;

            form.appendChild(input);
        }
    }

    document.getElementsByTagName("body")[0].appendChild(form);
    form.submit();
}

function selisihHari(a, b) {
    /*
        input: a = new Date('2023-06-10'), b = new Date('2023-06-05'). output: 5 (hari).
        input: a = new Date('2023-06-05'), b = new Date('2023-06-10'). output: -5 (minus lima hari).
        Jika mau selisihnya aja pakai Math.abs(selisihHari(a, b)) ya.
    */

    const _MS_PER_DAY = 1000 * 60 * 60 * 24;
    // Discard the time and time-zone information.
    const utc1 = Date.UTC(a.getFullYear(), a.getMonth(), a.getDate());
    const utc2 = Date.UTC(b.getFullYear(), b.getMonth(), b.getDate());

    return Math.floor((utc2 - utc1) / _MS_PER_DAY);
}

function toTitleCase(str) {
    return str.toLowerCase().replace(/(^|\s)\w/g, function (match) {
        return match.toUpperCase();
    });
}

String.prototype.toTitleCase = function () {
    return toTitleCase(this);
}