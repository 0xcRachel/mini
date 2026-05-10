import argparse
import itertools
import random
import unicodedata

random.seed(42)

GLOBAL_VALUES = {
    'amount': [
        '150.000đ', '180.000đ', '200.000đ', '220.000đ', '250.000đ', '280.000đ', '300.000đ',
        '320.000đ', '350.000đ', '380.000đ', '400.000đ', '450.000đ', '500.000đ', '550.000đ',
        '600.000đ', '650.000đ', '700.000đ', '750.000đ', '800.000đ', '900.000đ',
        '1.000.000đ', '1.200.000đ', '1.500.000đ', '2.000.000đ'
    ],
    'location': [
        'Hà Nội', 'Hồ Chí Minh', 'Đà Nẵng', 'Hải Phòng', 'Cần Thơ', 'Nha Trang', 'Vũng Tàu',
        'Bình Dương', 'Đồng Nai', 'Bắc Ninh', 'Bình Định', 'Thanh Hóa', 'Nghệ An', 'Phú Quốc',
        'Long An', 'Hậu Giang', 'Quảng Ninh', 'Quảng Nam', 'Gia Lai', 'Kon Tum'
    ],
    'product_type': [
        'điện thoại', 'laptop', 'máy tính bảng', 'tai nghe', 'loa bluetooth', 'chuột không dây',
        'bàn phím cơ', 'pin dự phòng', 'đồng hồ thông minh', 'camera hành trình', 'máy hút bụi',
        'máy lọc không khí', 'nồi chiên không dầu', 'smart TV', 'smartwatch', 'router wifi',
        'ổ cứng SSD', 'máy ảnh kỹ thuật số', 'máy chơi game', 'loa di động'
    ],
    'shipping_method': [
        'giao nhanh', 'giao tiêu chuẩn', 'giao tiết kiệm', 'giao hỏa tốc',
        'giao trong ngày', 'ship nội thành', 'ship ngoại tỉnh', 'vận chuyển nhanh'
    ],
    'support_type': [
        'hỗ trợ đặt hàng', 'hỗ trợ đổi trả', 'hỗ trợ bảo hành', 'tư vấn kỹ thuật',
        'tư vấn sản phẩm', 'hỗ trợ vận chuyển', 'hỗ trợ thanh toán', 'hỗ trợ hóa đơn'
    ],
    'tone': [
        'nhiệt tình', 'kỹ càng', 'chi tiết', 'dễ hiểu', 'thân thiện', 'chuyên nghiệp',
        'rõ ràng', 'chu đáo', 'nhanh chóng', 'đầy đủ'
    ],
    'issue': [
        'sản phẩm lỗi', 'thiếu phụ kiện', 'mất mã vận đơn', 'trễ giao hàng', 'ship bị hỏng',
        'đổi sai màu', 'thiếu phiếu bảo hành', 'không nhận được khuyến mãi', 'giao nhầm địa chỉ',
        'phí ship cao', 'vận chuyển chậm', 'bảo hành không nhận diện'
    ],
    'payment_method': [
        'COD', 'MoMo', 'VNPay', 'chuyển khoản ngân hàng', 'thẻ tín dụng',
        'thẻ ghi nợ', 'trả góp 0%', 'QR Pay', 'Apple Pay', 'Samsung Pay'
    ],
    'invoice_type': [
        'hóa đơn VAT', 'hóa đơn đỏ', 'hóa đơn GTGT', 'hóa đơn điện tử', 'biên nhận thu tiền'
    ],
    'order_number': [
        'DH12345', 'DH67890', 'TR99887', 'VN202405', 'SG001122', 'HN334455', 'SP202406'
    ],
    'selling_tone': ['ưu đãi', 'tiết kiệm', 'khuyến mãi', 'giá tốt']
}

CATEGORY_TEMPLATES = [
    {
        'topic': 'shipping_cost',
        'keywords': 'phí ship phí vận chuyển hỗ trợ ship giao hàng',
        'question_templates': [
            'Phí ship {product_type} về {location} với {shipping_method} là bao nhiêu?',
            'Giá vận chuyển {product_type} tới {location} khi mua {amount} là thế nào?',
            'Tính phí giao hàng {product_type} {amount} đến {location} ra sao?',
            'Mức phí ship cho đơn hàng {amount} gửi đến {location} với {shipping_method}?',
            'Cho tôi biết phí vận chuyển {product_type} từ kho tới {location} là bao nhiêu.',
            'Đơn {product_type} giá {amount} có bị tính phí ship cao không ở {location}?',
            'Ship {product_type} về {location} có được miễn phí nếu đơn {amount}?',
            'Hỏi về phí vận chuyển {product_type} tới {location} bằng {shipping_method}.',
            'Cần biết phí ship {product_type} tới {location} khi dùng {shipping_method}.',
            'Phiếu ship cho đơn {product_type} về {location} có giá bao nhiêu?',
        ],
        'answer_templates': [
            'Phí ship {product_type} về {location} thường dao động theo khu vực và giá trị đơn. Với đơn {amount}, phí có thể từ 0 đến 120.000đ, một số quận nội thành có thể miễn phí.',
            'Bảng phí vận chuyển đến {location} được tính theo trọng lượng và loại sản phẩm. Đơn {amount} {product_type} thường chỉ mất khoảng 30.000đ - 80.000đ nếu chọn {shipping_method}.',
            'Đối với {product_type} về {location}, phí ship sẽ thay đổi tùy khu vực. Nếu đơn từ 500.000đ, cửa hàng thường hỗ trợ miễn phí hoặc giảm mạnh chi phí.',
            'Cửa hàng tính phí ship {product_type} {amount} về {location} căn bản trên tuyến đường và dịch vụ, thông thường không quá 100.000đ với {shipping_method}.',
            'Thông thường, đơn {amount} giao về {location} sẽ có phí khoảng 20.000đ-60.000đ. Một số khu vực xa hơn phải mất phí cao hơn hoặc hỗ trợ miễn phí cho đơn lớn.',
        ],
        'params': ['product_type', 'location', 'shipping_method', 'amount']
    },
    {
        'topic': 'free_shipping',
        'keywords': 'miễn phí ship miễn phí vận chuyển điều kiện miễn ship',
        'question_templates': [
            'Đơn hàng bao nhiêu mới được miễn phí ship {location}?',
            'Cửa hàng áp dụng miễn phí ship với đơn từ {amount} trở lên đúng không?',
            'Miễn phí giao hàng khi mua {product_type} có giá {amount} được không?',
            'Tôi muốn biết điều kiện miễn phí ship cho {product_type} gửi tới {location}.',
            'Có chương trình miễn phí vận chuyển cho đơn hàng {amount} không?',
        ],
        'answer_templates': [
            'Miễn phí ship áp dụng cho đơn hàng từ 500.000đ ở nội thành Hà Nội và Hồ Chí Minh. Với đơn từ {amount}, nếu ở ngoại tỉnh vẫn có thể được hỗ trợ một phần phí.',
            'Nếu đơn {amount} mua {product_type}, bạn sẽ được miễn phí ship ở khu vực nội thành. Ngoại tỉnh có thể tính phí tùy vị trí.',
            'Điều kiện miễn phí ship là đơn từ 500.000đ trở lên hoặc chương trình khuyến mãi. Cửa hàng hỗ trợ thêm với một số tuyến giao hàng đặc biệt.',
        ],
        'params': ['amount', 'product_type', 'location']
    },
    {
        'topic': 'delivery_time',
        'keywords': 'thời gian giao hàng ship bao lâu giao nhanh',
        'question_templates': [
            'Giao hàng tới {location} mất bao nhiêu ngày với {shipping_method}?',
            'Đơn hàng {product_type} gửi về {location} khi nào nhận được?',
            'Thời gian vận chuyển {product_type} tới {location} là bao lâu?',
            'Ship {product_type} {selling_tone} đến {location} mất mấy ngày?',
            'Khi nào tôi nhận được đơn đặt {amount} tại {location}?',
        ],
        'answer_templates': [
            'Thời gian giao hàng về {location} thường là 1-2 ngày với nội thành và 2-4 ngày với ngoại tỉnh. Nếu chọn {shipping_method}, có thể nhanh hơn hoặc trễ thêm tùy tình huống.',
            'Đơn {product_type} đến {location} sẽ về trong khoảng 1-4 ngày. Với khu vực vùng sâu vùng xa, thời gian có thể kéo dài 5-7 ngày.',
            'Nếu bạn chọn {shipping_method}, đơn hàng thường đến nhanh nhất 1 ngày nội thành, hoặc 3-5 ngày với ngoại tỉnh. Thời gian chính xác phụ thuộc đơn vị vận chuyển.',
        ],
        'params': ['location', 'shipping_method', 'product_type', 'amount', 'selling_tone']
    },
    {
        'topic': 'order_tracking',
        'keywords': 'theo dõi đơn hàng tra cứu trạng thái mã vận đơn',
        'question_templates': [
            'Làm sao để theo dõi đơn hàng {product_type}?',
            'Tôi kiểm tra trạng thái đơn {order_number} như thế nào?',
            'Cách tra cứu mã vận đơn khi giao tới {location}?',
            'Sao tôi không thấy mã đơn hàng sau khi đặt {amount}?',
            'Theo dõi đơn giao hàng có mất phí không?',
        ],
        'answer_templates': [
            'Bạn kiểm tra đơn hàng bằng mã vận đơn được gửi qua SMS hoặc email. Nếu chưa nhận mã, liên hệ hotline hoặc chat để kiểm tra ngay.',
            'Đơn {product_type} có thể tra cứu trực tiếp trên website hoặc zalo của cửa hàng bằng mã đơn {order_number}. Nếu không có mã, nhân viên sẽ hỗ trợ cung cấp.',
            'Khi đặt hàng, hệ thống sẽ gửi mã vận đơn. Bạn dùng mã này để theo dõi trạng thái và vị trí đơn trên trang nhà vận chuyển.',
        ],
        'params': ['product_type', 'order_number', 'location', 'amount']
    },
    {
        'topic': 'return_policy',
        'keywords': 'chính sách đổi trả đổi trả hoàn tiền',
        'question_templates': [
            'Chính sách đổi trả cho {product_type} như thế nào?',
            'Tôi muốn đổi trả vì {issue} thì cần làm gì?',
            'Đổi trả trong bao lâu sau khi nhận hàng?',
            'Điều kiện đổi trả sản phẩm lỗi có yêu cầu gì?',
            'Cửa hàng hỗ trợ đổi trả ở khu vực {location} không?',
        ],
        'answer_templates': [
            'Cửa hàng hỗ trợ đổi trả trong 7 ngày nếu sản phẩm lỗi do nhà sản xuất hoặc giao sai. Bạn cần giữ nguyên hộp, tem mác và phụ kiện đi kèm.',
            'Khi gặp {issue}, bạn có thể gửi yêu cầu đổi trả qua hotline hoặc chat để nhân viên hướng dẫn quy trình cụ thể và thời gian lấy hàng.',
            'Đổi trả được chấp nhận nếu sản phẩm không bị hư hỏng do sử dụng sai. Nếu lỗi kỹ thuật, chúng tôi sẽ đổi mới hoặc hoàn tiền theo chính sách.',
        ],
        'params': ['product_type', 'issue', 'location']
    },
    {
        'topic': 'warranty',
        'keywords': 'bảo hành chính hãng bảo hành 1 đổi 1',
        'question_templates': [
            'Bảo hành {product_type} trong bao lâu?',
            'Sản phẩm lỗi có được bảo hành 1 đổi 1 không?',
            'Điều kiện nhận bảo hành chính hãng là gì?',
            'Tôi cần những gì để làm bảo hành {product_type}?',
            'Bảo hành tại {location} có hỗ trợ không?',
        ],
        'answer_templates': [
            'Sản phẩm được bảo hành chính hãng theo quy định nhà sản xuất, thường 12 tháng đối với điện thoại và laptop, 6 tháng đối với phụ kiện. Chúng tôi hỗ trợ 1 đổi 1 trong 30 ngày nếu lỗi do nhà sản xuất.',
            'Để bảo hành, bạn cần giữ hóa đơn và phiếu bảo hành. Nếu mua từ chúng tôi, nhân viên sẽ hướng dẫn chi tiết hồ sơ cần chuẩn bị.',
            'Bảo hành có thể xử lý tại cửa hàng hoặc trung tâm bảo hành chính hãng. Hãy giữ lại biên nhận để được ưu tiên xử lý nhanh.',
        ],
        'params': ['product_type', 'location']
    },
    {
        'topic': 'hotline_support',
        'keywords': 'hotline hỗ trợ khách hàng chăm sóc khách hàng',
        'question_templates': [
            'Số hotline hỗ trợ khách hàng là gì?',
            'Liên hệ bộ phận chăm sóc khách hàng qua kênh nào?',
            'Tôi cần hỗ trợ {support_type} thì gọi số nào?',
            'Hotline mở cửa từ mấy giờ tới mấy giờ?',
            'Chuyên viên tư vấn hỗ trợ mua hàng có số điện thoại không?',
        ],
        'answer_templates': [
            'Hotline hỗ trợ của chúng tôi là 1800-1234, phục vụ 8h00-20h00 mỗi ngày. Bạn cũng có thể chat trực tiếp hoặc gửi email để được hỗ trợ.',
            'Với yêu cầu {support_type}, xin vui lòng gọi 1800-1234 hoặc nhắn tin qua fanpage để kết nối tư vấn viên ngay.',
            'Đội ngũ chăm sóc khách hàng luôn sẵn sàng hỗ trợ. Nếu bạn cần hỗ trợ gấp, hãy gọi hotline trong giờ hành chính để được giải đáp nhanh chóng.',
        ],
        'params': ['support_type', 'location']
    },
    {
        'topic': 'payment_methods',
        'keywords': 'thanh toán thanh toán qua MoMo VNPay COD',
        'question_templates': [
            'Cửa hàng nhận thanh toán {payment_method} không?',
            'Tôi có thể trả góp {product_type} bằng {payment_method} không?',
            'Phương thức thanh toán nào nhanh nhất?',
            'Có thể chuyển khoản ngân hàng ngay hay phải chờ xác nhận?',
            'Thanh toán COD có giới hạn khu vực không?',
        ],
        'answer_templates': [
            'Chúng tôi hỗ trợ thanh toán {payment_method}, COD, chuyển khoản và trả góp 0%. Với lựa chọn {payment_method}, đơn hàng sẽ được xử lý ngay khi xác nhận thành công.',
            'Thanh toán {payment_method} được chấp nhận với hầu hết mọi đơn và rất tiện lợi. Nếu cần trả góp, nhân viên sẽ giải thích các gói phù hợp.',
            'Bạn có thể chọn phương thức phù hợp: COD, chuyển khoản, MoMo, VNPay hoặc trả góp. Mỗi phương thức có chính sách xử lý thời gian khác nhau.',
        ],
        'params': ['payment_method', 'product_type']
    },
    {
        'topic': 'invoice_vat',
        'keywords': 'hóa đơn VAT in hóa đơn xuất hóa đơn',
        'question_templates': [
            'Cửa hàng có xuất {invoice_type} không?',
            'Làm sao để nhận hóa đơn {invoice_type}?',
            'Tôi cần gửi thông tin công ty để lấy hóa đơn {invoice_type}.',
            'Hóa đơn {invoice_type} có tính phí không?',
            'Xin báo giá có kèm hóa đơn {invoice_type} được không?',
        ],
        'answer_templates': [
            'Chúng tôi có thể xuất {invoice_type} đầy đủ khi yêu cầu. Vui lòng cung cấp tên công ty và mã số thuế trước khi giao hàng.',
            'Nếu cần hóa đơn {invoice_type}, hãy đặt ghi chú khi hoàn tất đơn và nhân viên sẽ liên hệ xác nhận thông tin.',
            'Hóa đơn {invoice_type} được cung cấp miễn phí cho khách hàng doanh nghiệp khi mua hàng chính hãng.',
        ],
        'params': ['invoice_type', 'product_type']
    },
    {
        'topic': 'product_authenticity',
        'keywords': 'hàng chính hãng cam kết nguồn gốc sản phẩm',
        'question_templates': [
            'Sản phẩm {product_type} có phải hàng chính hãng không?',
            'Có đảm bảo không bán hàng dựng hay fake không?',
            'Cửa hàng có giấy tờ, xuất xứ cho {product_type} không?',
            'Sản phẩm mua tại đây có bảo hành chính hãng không?',
            'Tôi cần xác thực nguồn gốc {product_type}.',
        ],
        'answer_templates': [
            'ABC Trading cam kết 100% hàng chính hãng, có hóa đơn và bảo hành đầy đủ. Chúng tôi không bán hàng dựng hoặc hàng nhái.',
            'Mỗi {product_type} đều được nhập chính hãng, kèm phiếu bảo hành và hóa đơn nếu khách yêu cầu.',
            'Bạn hoàn toàn yên tâm, sản phẩm từ chúng tôi có nguồn gốc rõ ràng và chính sách bảo hành minh bạch.',
        ],
        'params': ['product_type']
    },
    {
        'topic': 'address_change',
        'keywords': 'đổi địa chỉ giao hàng thay đổi thông tin đơn hàng',
        'question_templates': [
            'Tôi muốn đổi địa chỉ nhận hàng sau khi đặt đơn, làm sao?',
            'Đổi địa chỉ giao hàng tại {location} có thực hiện được không?',
            'Sửa thông tin nhận hàng có mất phí không?',
            'Đổi địa chỉ trước khi đóng gói đơn được không?',
            'Nếu giao nhầm địa chỉ thì xử lý thế nào?',
        ],
        'answer_templates': [
            'Bạn có thể đổi địa chỉ giao hàng miễn phí trước khi đơn được đóng gói. Hãy liên hệ ngay hotline hoặc chat để nhân viên cập nhật.',
            'Nếu đơn vẫn chưa xuất kho, cửa hàng sẽ hỗ trợ thay đổi địa chỉ. Trong trường hợp đã xuất kho, cần liên hệ càng sớm càng tốt để xử lý.',
            'Đổi thông tin nhận hàng không mất phí nếu yêu cầu trong thời gian cho phép trước khi giao bưu tá.',
        ],
        'params': ['location']
    },
    {
        'topic': 'exchange_shipping',
        'keywords': 'đổi trả vận chuyển phí đổi trả đổi trả miễn phí',
        'question_templates': [
            'Phí ship đổi trả có được tính không?',
            'Đổi trả hàng lỗi thì cửa hàng hỗ trợ vận chuyển như thế nào?',
            'Gửi trả hàng có mất tiền ship không?',
            'Cửa hàng thu phí vận chuyển đổi trả hay không?',
            'Đổi trả {product_type} nếu bị lỗi có được miễn phí ship?',
        ],
        'answer_templates': [
            'Thường thì đổi trả do lỗi nhà sản xuất sẽ được miễn phí ship. Hãy gửi yêu cầu trước để nhân viên hướng dẫn quy trình lấy hàng.',
            'Nếu đổi trả vì nguyên nhân chủ quan, phí ship có thể do khách chịu. Với lỗi kỹ thuật, chúng tôi sẽ hỗ trợ free ship.',
            'Đổi trả sản phẩm lỗi nhận được hỗ trợ vận chuyển. Chúng tôi sẽ liên hệ để thu hồi hàng và đổi hàng mới nếu đủ điều kiện.',
        ],
        'params': ['product_type']
    },
    {
        'topic': 'installation_help',
        'keywords': 'hướng dẫn lắp đặt hỗ trợ cài đặt hướng dẫn sử dụng',
        'question_templates': [
            'Cửa hàng có hỗ trợ lắp đặt {product_type} tại nhà không?',
            'Tôi cần hướng dẫn sử dụng {product_type} mới mua.',
            'Cách cài đặt thiết bị {product_type} như thế nào?',
            'Có dịch vụ setup tại chỗ không?',
            'Tư vấn kết nối {product_type} với mạng wifi ra sao?',
        ],
        'answer_templates': [
            'Cửa hàng hỗ trợ hướng dẫn sử dụng và cài đặt cơ bản. Nếu cần lắp đặt tại nhà, vui lòng gọi hotline để kiểm tra dịch vụ tại khu vực bạn.',
            'Chúng tôi có thể gửi video hướng dẫn hoặc hướng dẫn trực tiếp qua chat để bạn sử dụng {product_type} nhanh chóng.',
            'Với yêu cầu cấu hình, nhân viên kỹ thuật sẽ hỗ trợ qua điện thoại hoặc đến tận nơi nếu bạn chọn dịch vụ lắp đặt.',
        ],
        'params': ['product_type']
    }
]

OPEN_ENDED_TEMPLATES = [
    'Tôi cần trợ giúp như một chuyên viên tư vấn: nên chọn phương án nào để ship {product_type} về {location} tiết kiệm?',
    'Cho tôi lời khuyên chuyên sâu về phí giao hàng, đổi trả và bảo hành khi mua {product_type}.',
    'Tôi muốn bạn trả lời như cố vấn dịch vụ khách hàng, giải thích rõ điều kiện miễn phí ship và bảo hành.',
    'Nếu không có dữ liệu trực tiếp, hãy đề xuất phương án bán hàng phù hợp cho đơn {product_type} {amount}.',
    'Hãy tư vấn giúp tôi cách xử lý khi đơn {product_type} bị trễ giao và cần đổi địa chỉ.',
    'Tôi muốn bạn nghĩ rộng và trả lời như chuyên viên hỗ trợ, dùng lịch sử chat để hiểu yêu cầu.',
    'Cung cấp cho tôi phương án xử lý khi khách hỏi về ship, trả hàng, thanh toán và bảo hành trong cùng một câu.',
    'Làm ơn giải thích bằng tiếng Việt đơn giản và rõ ràng giống tư vấn viên, về phí ship và điều kiện đổi trả.',
    'Bạn có thể đưa ra kịch bản phục vụ khách hàng khi họ thắc mắc phí vận chuyển và bảo hành {product_type}?',
    'Tôi muốn câu trả lời có sắc thái hỗ trợ, đúng kiểu giải đáp vấn đề tổng quan yêu cầu.',
]

OPEN_ENDED_ANSWERS = [
    'Nếu tôi ở vị trí tư vấn, tôi sẽ giải thích rằng phí ship dựa trên giá trị đơn và địa chỉ, rồi nhấn mạnh điều kiện miễn phí ship và cách liên hệ khi cần hỗ trợ đổi trả.',
    'Câu trả lời nên tập trung vào ba điểm: phí vận chuyển, thời gian giao hàng và quyền lợi đổi trả/bảo hành, để khách cảm thấy yên tâm.',
    'Hãy trả lời như một chuyên viên chăm sóc khách hàng, nhắc khách lưu giữ thông tin đơn hàng và nếu cần hỗ trợ thêm thì liên hệ ngay hotline.',
    'Trường hợp chưa có dữ liệu cụ thể, bạn nên đưa ra giải pháp chung và hướng dẫn khách lục lại lịch sử chat hoặc yêu cầu bổ sung thông tin.',
    'Nhận định đơn giản: miễn phí ship nếu đơn lớn, order trước giờ cut-off để giao nhanh, và giữ giấy tờ bảo hành để giải quyết sau này.',
]


def normalize_text(text: str) -> str:
    normalized = unicodedata.normalize('NFC', text)
    return normalized.replace("'", "''").replace('\n', ' ').strip()


def build_keywords(base_keywords: str, params: dict) -> str:
    extras = []
    for value in params.values():
        if isinstance(value, str):
            extras.extend(value.split())
    tokens = set(base_keywords.split() + extras)
    return ' '.join(sorted(tokens))


def generate_entries(limit=400000):
    entries = []
    questions = set()
    entry_id = 1

    open_ended_target = int(limit * 0.2)
    while entry_id <= open_ended_target:
        template = random.choice(OPEN_ENDED_TEMPLATES)
        params = {
            'product_type': random.choice(GLOBAL_VALUES['product_type']),
            'location': random.choice(GLOBAL_VALUES['location']),
            'amount': random.choice(GLOBAL_VALUES['amount']),
        }
        question = template.format(**params)
        if question in questions:
            continue
        questions.add(question)
        answer = random.choice(OPEN_ENDED_ANSWERS).format(**params)
        keywords = build_keywords('tư vấn hỗ trợ ship bảo hành đổi trả', params)
        entries.append((entry_id, question, keywords, answer))
        entry_id += 1

    for category in CATEGORY_TEMPLATES:
        param_names = category['params']
        value_lists = [GLOBAL_VALUES[name] for name in param_names]
        for template in category['question_templates']:
            for combo in itertools.product(*value_lists):
                if entry_id > limit:
                    return entries
                params = dict(zip(param_names, combo))
                question = template.format(**params)
                if question in questions:
                    continue
                questions.add(question)
                answer = random.choice(category['answer_templates']).format(**params)
                keywords = build_keywords(category['keywords'], params)
                entries.append((entry_id, question, keywords, answer))
                entry_id += 1
            if entry_id > limit:
                return entries

    if entry_id <= limit:
        raise ValueError(f'Chỉ tạo được {entry_id - 1} mục, cần {limit}')
    return entries


def write_sql(entries, output_file='faqs_400k.sql'):
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('-- Generated FAQ dataset for ABC Trading support\n')
        f.write('-- Entries: {}\n\n'.format(len(entries)))
        f.write('INSERT INTO `faqs` (`id`, `keywords`, `question`, `answer`) VALUES\n')
        for index, (entry_id, question, keywords, answer) in enumerate(entries, start=1):
            line = (
                f"({entry_id}, '{normalize_text(keywords)}', '{normalize_text(question)}', '{normalize_text(answer)}')"
            )
            line += ',\n' if index < len(entries) else ';\n'
            f.write(line)


def parse_args():
    parser = argparse.ArgumentParser(description='Generate a large FAQ dataset for support and shipping queries.')
    parser.add_argument('--limit', type=int, default=400000, help='Number of FAQ entries to generate.')
    parser.add_argument('--output', type=str, default='faqs_400k.sql', help='Output SQL filename.')
    return parser.parse_args()


if __name__ == '__main__':
    args = parse_args()
    entries = generate_entries(limit=args.limit)
    write_sql(entries, output_file=args.output)
    print(f'Generated {args.output} with {len(entries)} entries.')
