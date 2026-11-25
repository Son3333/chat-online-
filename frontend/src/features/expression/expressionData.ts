import { StickerPack, GifItem } from '../../types';

// Hàm chuẩn hóa tiếng Việt loại bỏ dấu để tìm kiếm không dấu
export function removeVietnameseTones(str: string): string {
  return str
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .replace(/đ/g, 'd')
    .replace(/Đ/g, 'D')
    .toLowerCase()
    .trim();
}

// 1. KHO EMOJI TIÊU CHUẨN ĐẦY ĐỦ PHÂN THEO 8 DANH MỤC
export interface EmojiCategory {
  id: string;
  name: string;
  icon: string;
  emojis: { char: string; name: string; keywords: string[] }[];
}

export const EMOJI_CATEGORIES: EmojiCategory[] = [
  {
    id: 'smileys',
    name: 'Mặt cười & Cảm xúc',
    icon: '😀',
    emojis: [
      { char: '😀', name: 'Cười tươi', keywords: ['cuoi', 'vui', 'smile', 'happy'] },
      { char: '😃', name: 'Cười mở to mắt', keywords: ['cuoi', 'vui', 'haha'] },
      { char: '😄', name: 'Cười tít mắt', keywords: ['cuoi', 'vui', 'haha', 'hihi'] },
      { char: '😁', name: 'Cười toe toét', keywords: ['cuoi', 'grin'] },
      { char: '😆', name: 'Cười sặc sụa', keywords: ['cuoi', 'haha', 'chet cuoi'] },
      { char: '😅', name: 'Cười trừ toát mồ hôi', keywords: ['ngai', 'sweat', 'cuoi tru'] },
      { char: '🤣', name: 'Cười lăn lộn', keywords: ['rofl', 'haha', 'lan lon', 'hai'] },
      { char: '😂', name: 'Cười ra nước mắt', keywords: ['cuoi', 'haha', 'nuoc mat', 'lol'] },
      { char: '🙂', name: 'Cười mỉm', keywords: ['nhe nhang', 'mim cuoi'] },
      { char: '😉', name: 'Nháy mắt', keywords: ['nhay mat', 'wink', 'tinh'] },
      { char: '😊', name: 'Cười bẽn lẽn', keywords: ['ngai ngung', 'de thuong', 'blush'] },
      { char: '😇', name: 'Thiên thần tốt bụng', keywords: ['thien than', 'ngoan', 'nguoi tot'] },
      { char: '🥰', name: 'Ngập tràn tình yêu', keywords: ['yeu', 'love', 'tim', 'thuong'] },
      { char: '😍', name: 'Mắt hình trái tim', keywords: ['yeu', 'me', 'thich', 'love'] },
      { char: '🤩', name: 'Mắt ngôi sao ngỡ ngàng', keywords: ['ngau', 'sao', 'dinh cao', 'wow'] },
      { char: '😘', name: 'Thổi nụ hôn', keywords: ['hon', 'kiss', 'yeu', 'moa'] },
      { char: '😋', name: 'Ngon miệng', keywords: ['ngon', 'them an', 'the luoi'] },
      { char: '😜', name: 'Lè lưỡi nháy mắt', keywords: ['treu', 'hai huoc', 'choc'] },
      { char: '🤪', name: 'Khuôn mặt ngáo', keywords: ['ngao', 'dien', 'hai'] },
      { char: '😎', name: 'Đeo kính ngầu', keywords: ['ngau', 'cool', 'chat', 'dang cap'] },
      { char: '🥳', name: 'Tiệc tùng ăn mừng', keywords: ['an mung', 'party', 'sinh nhat', 'chuc mung'] },
      { char: '😏', name: 'Cười khẩy nguy hiểm', keywords: ['nguy hiem', 'smirk', 'cuoi khey'] },
      { char: '😒', name: 'Chán nản không thèm nói', keywords: ['chan', 'kho chiu', 'meh'] },
      { char: '😞', name: 'Thất vọng', keywords: ['buon', 'that vong', 'sad'] },
      { char: '😔', name: 'Trầm ngâm buồn tủi', keywords: ['buon', 'suy tu', 'tram cam'] },
      { char: '😟', name: 'Lo lắng', keywords: ['lo lang', 'bat an', 'worried'] },
      { char: '🥺', name: 'Mắt long lanh năn nỉ', keywords: ['nan ni', 'xin', 'de thuong', 'thuong'] },
      { char: '😢', name: 'Rơi một giọt lệ', keywords: ['buon', 'khoc', 'rot nuoc mat'] },
      { char: '😭', name: 'Khóc toáng lên', keywords: ['khoc', 'huhu', 'dau long', 'sad'] },
      { char: '😤', name: 'Thở phì khói mũi', keywords: ['bực', 'tuc gian', 'kho chiu'] },
      { char: '😠', name: 'Tức giận', keywords: ['tuc', 'gian', 'angry'] },
      { char: '😡', name: 'Mặt đỏ bừng giận dữ', keywords: ['gian du', 'dien len', 'rage'] },
      { char: '🤬', name: 'Chửi bới phẫn nộ', keywords: ['chui', 'tuc gian', 'phan no'] },
      { char: '🤯', name: 'Nổ tung não', keywords: ['no nao', 'kinh ngac', 'mind blown'] },
      { char: '😳', name: 'Đỏ mặt ngượng ngùng', keywords: ['nguong', 'xau ho', 'soc'] },
      { char: '🥵', name: 'Nóng bức toát mồ hôi', keywords: ['nong', 'hot', 'toat mo hoi'] },
      { char: '🥶', name: 'Lạnh buốt cóng', keywords: ['lanh', 'ret', 'cold'] },
      { char: '😱', name: 'Hét lên vì sợ hãi', keywords: ['het', 'so', 'kinh hoang', 'hoang hot'] },
      { char: '🤔', name: 'Suy nghĩ trầm ngâm', keywords: ['suy nghi', 'tinh toan', 'think'] },
      { char: '🤗', name: 'Vòng tay ôm ấm áp', keywords: ['om', 'hug', 'yeu thuong'] },
      { char: '🤫', name: 'Suỵt giữ bí mật', keywords: ['suyt', 'bi mat', 'im lang'] },
      { char: '😴', name: 'Ngủ say giấc', keywords: ['ngu', 'di ngu', 'ngu ngon', 'sleep'] },
    ],
  },
  {
    id: 'gestures',
    name: 'Bàn tay & Cử chỉ',
    icon: '👍',
    emojis: [
      { char: '👍', name: 'Tuyệt vời / Thích', keywords: ['like', 'ok', 'tot', 'dong y', 'dinh'] },
      { char: '👎', name: 'Không thích / Kém', keywords: ['dislike', 'te', 'che'] },
      { char: '👌', name: 'Số dách / Chuẩn', keywords: ['ok', 'chuan', 'hoan hao'] },
      { char: '✌️', name: 'Chiến thắng / Hòa bình', keywords: ['peace', 'chien thang', 'hi'] },
      { char: '🤞', name: 'Cầu may mắn', keywords: ['may man', 'chuc may man', 'hope'] },
      { char: '🤟', name: 'Tôi yêu bạn', keywords: ['yeu', 'love you', 'ily'] },
      { char: '🤘', name: 'Bung lụa Rock', keywords: ['rock', 'chay', 'ngau'] },
      { char: '🤙', name: 'Gọi tôi nhé', keywords: ['call me', 'alo', 'keo'] },
      { char: '👋', name: 'Vẫy tay chào', keywords: ['chao', 'hello', 'hi', 'tam biet', 'bye'] },
      { char: '🤝', name: 'Bắt tay hợp tác', keywords: ['hop tac', 'chot keo', 'dong y', 'dong long'] },
      { char: '💪', name: 'Cố lên / Sức mạnh', keywords: ['co len', 'manh me', 'quyet tam', 'khoe'] },
      { char: '👏', name: 'Vỗ tay tán thưởng', keywords: ['vo tay', 'khen', 'tuyet', 'chuc mung'] },
      { char: '🙌', name: 'Nâng tay ăn mừng', keywords: ['hoan ho', 'an mung', 'tuyet voi'] },
      { char: '🙏', name: 'Chắp tay cảm ơn / Cầu nguyện', keywords: ['cam on', 'xin loi', 'cau nguyen', 'biet on', 'pls'] },
      { char: '✍️', name: 'Đang ghi chép', keywords: ['viet', 'ghi chep', 'hoc tap'] },
      { char: '💅', name: 'Sơn móng tay chảnh', keywords: ['chanh', 'slay', 'dieu'] },
    ],
  },
  {
    id: 'hearts',
    name: 'Trái tim & Tình cảm',
    icon: '❤️',
    emojis: [
      { char: '❤️', name: 'Trái tim đỏ', keywords: ['tim', 'yeu', 'love', 'do'] },
      { char: '💖', name: 'Trái tim lấp lánh', keywords: ['yeu', 'tim', 'lap lanh'] },
      { char: '💕', name: 'Hai trái tim bên nhau', keywords: ['tinh yeu', 'yeu', 'cap doi'] },
      { char: '💞', name: 'Trái tim quay tròn', keywords: ['yeu', 'rung dong', 'thich'] },
      { char: '💓', name: 'Trái tim đập thổn thức', keywords: ['tim dap', 'nho', 'rung dong'] },
      { char: '💗', name: 'Trái tim lớn dần', keywords: ['yeu thuong', 'quan tam'] },
      { char: '💘', name: 'Mũi tên tình yêu Cupid', keywords: ['trung tieng set', 'cupid', 'yeu'] },
      { char: '💝', name: 'Trái tim ruy băng quà tặng', keywords: ['qua tang', 'yeu', 'danh cho ban'] },
      { char: '💔', name: 'Trái tim tan vỡ', keywords: ['that tinh', 'dau long', 'chia tay', 'tan vo'] },
      { char: '💯', name: '100 điểm tuyệt đối', keywords: ['100', 'chuan', 'hoan hao', 'dinh'] },
      { char: '🔥', name: 'Ngọn lửa nhiệt huyết', keywords: ['chay', 'hot', 'nong', 'dinh', 'chay pho'] },
      { char: '✨', name: 'Ánh sáng lấp lánh', keywords: ['lap lanh', 'sao', 'dep', 'toa sang'] },
      { char: '⭐', name: 'Ngôi sao vàng', keywords: ['ngoi sao', 'star', 'khen'] },
      { char: '🎉', name: 'Pháo hoa tiệc tùng', keywords: ['chuc mung', 'phao hoa', 'party', 'sinh nhat'] },
    ],
  },
  {
    id: 'animals',
    name: 'Động vật dễ thương',
    icon: '🐱',
    emojis: [
      { char: '🐶', name: 'Chú chó đáng yêu', keywords: ['cho', 'dog', 'cun'] },
      { char: '🐱', name: 'Mèo con meo meo', keywords: ['meo', 'cat', 'meomeo'] },
      { char: '🐼', name: 'Gấu trúc lười', keywords: ['gau truc', 'panda'] },
      { char: '🐻', name: 'Gấu nâu', keywords: ['gau', 'bear'] },
      { char: '🐰', name: 'Thỏ trắng nhanh nhẹn', keywords: ['tho', 'rabbit'] },
      { char: '🦊', name: 'Cáo thông minh', keywords: ['cao', 'fox'] },
      { char: '🐯', name: 'Hổ dũng mãnh', keywords: ['ho', 'tiger'] },
      { char: '🦁', name: 'Sư tử chúa sơn lâm', keywords: ['su tu', 'lion'] },
      { char: '🐧', name: 'Chim cánh cụt', keywords: ['canh cut', 'penguin'] },
      { char: '🐥', name: 'Gà con líu lo', keywords: ['ga', 'chick', 'chip'] },
      { char: '🐷', name: 'Heo con ủn ỉn', keywords: ['heo', 'pig', 'lon'] },
      { char: '🐸', name: 'Ếch xanh meme', keywords: ['ech', 'frog', 'pepe'] },
    ],
  },
  {
    id: 'food',
    name: 'Đồ ăn & Thức uống',
    icon: '☕',
    emojis: [
      { char: '☕', name: 'Cà phê nóng', keywords: ['ca phe', 'coffee', 'sang'] },
      { char: '🍵', name: 'Trà xanh thư giãn', keywords: ['tra', 'tea'] },
      { char: '🧋', name: 'Trà sữa trân châu', keywords: ['tra sua', 'boba', 'uong tra sua'] },
      { char: '🍺', name: 'Bia lạnh cạn ly', keywords: ['bia', 'nhau', 'cheers', 'uong'] },
      { char: '🍻', name: 'Nâng ly chúc mừng', keywords: ['nang ly', 'nhau', 'dzô'] },
      { char: '🎂', name: 'Bánh sinh nhật', keywords: ['banh sinh nhat', 'cake', 'hpbd', 'chuc mung'] },
      { char: '🍕', name: 'Pizza phô mai', keywords: ['pizza', 'do an', 'an'] },
      { char: '🍔', name: 'Burger kẹp thịt', keywords: ['burger', 'an nhanh'] },
      { char: '🍜', name: 'Bát phở / Mì nóng', keywords: ['pho', 'mi', 'an sang', 'an trua'] },
      { char: '🍦', name: 'Kem mát lạnh', keywords: ['kem', 'ice cream', 'ngot'] },
      { char: '🍎', name: 'Táo đỏ tươi', keywords: ['tao', 'apple', 'hoa qua'] },
      { char: '🍓', name: 'Dâu tây ngọt ngào', keywords: ['dau tay', 'strawberry'] },
    ],
  },
];

// 2. KHO BỘ SƯU TẬP STICKER PHONG PHÚ (SVG / Animated WebP / PNG chuẩn Vector)
export const DEFAULT_STICKER_PACKS: StickerPack[] = [
  {
    id: 'bubu-dudu',
    name: 'Mèo Bubu Dudu Cute',
    author: 'Vibe Studio',
    category: 'Động vật dễ thương',
    avatarUrl: 'https://api.dicebear.com/7.x/bottts/svg?seed=bubu-cover&backgroundColor=ffd5dc',
    description: 'Bộ sticker mèo chibi đáng yêu với vô vàn biểu cảm thả thính, hờn dỗi, ôm ấp.',
    isInstalled: true,
    stickers: [
      {
        id: 'bubu-1',
        name: 'Bắn tim yêu thương',
        url: 'https://api.dicebear.com/7.x/bottts/svg?seed=bubu-love&backgroundColor=ffb3c1',
        keywords: ['yeu', 'love', 'tim', 'thuong', 'moa', 'hon'],
        isAnimated: true,
      },
      {
        id: 'bubu-2',
        name: 'Cười lăn lộn hihi',
        url: 'https://api.dicebear.com/7.x/bottts/svg?seed=bubu-haha&backgroundColor=ffe5b4',
        keywords: ['haha', 'cuoi', 'vui', 'hihi', 'hai'],
        isAnimated: false,
      },
      {
        id: 'bubu-3',
        name: 'Khóc nhè tủi thân',
        url: 'https://api.dicebear.com/7.x/bottts/svg?seed=bubu-sad&backgroundColor=cce3de',
        keywords: ['buon', 'khoc', 'huhu', 'sad', 'tui than'],
        isAnimated: true,
      },
      {
        id: 'bubu-4',
        name: 'Vẫy tay chào bạn',
        url: 'https://api.dicebear.com/7.x/bottts/svg?seed=bubu-wave&backgroundColor=e2eafc',
        keywords: ['chao', 'hello', 'hi', 'tam biet', 'bye'],
        isAnimated: false,
      },
      {
        id: 'bubu-5',
        name: 'Chúc ngủ ngon đắp chăn',
        url: 'https://api.dicebear.com/7.x/bottts/svg?seed=bubu-sleep&backgroundColor=d8e2dc',
        keywords: ['ngu ngon', 'g9', 'di ngu', 'sleep'],
        isAnimated: true,
      },
      {
        id: 'bubu-6',
        name: 'Bối rối gãi đầu',
        url: 'https://api.dicebear.com/7.x/bottts/svg?seed=bubu-confused&backgroundColor=fcd5ce',
        keywords: ['ngai', 'xin loi', 'boi roi', 'sorry'],
        isAnimated: false,
      },
      {
        id: 'bubu-7',
        name: 'Giận tím người',
        url: 'https://api.dicebear.com/7.x/bottts/svg?seed=bubu-angry&backgroundColor=ffccd5',
        keywords: ['gian', 'tuc', 'kho chiu', 'gian tim nguoi'],
        isAnimated: true,
      },
      {
        id: 'bubu-8',
        name: 'Cảm ơn chắp tay',
        url: 'https://api.dicebear.com/7.x/bottts/svg?seed=bubu-thanks&backgroundColor=f0efeb',
        keywords: ['cam on', 'thank', 'tks', 'biet on'],
        isAnimated: false,
      },
    ],
  },
  {
    id: 'quynh-aka-meme',
    name: 'Meme Hài Hước Việt Nam',
    author: 'Cộng đồng Vibe',
    category: 'Meme tiếng Việt',
    avatarUrl: 'https://api.dicebear.com/7.x/fun-emoji/svg?seed=quynh-cover&backgroundColor=fef08a',
    description: 'Tuyển tập biểu cảm bựa hài, lầy lội cực kỳ thích hợp để cà khịa bạn bè.',
    isInstalled: true,
    stickers: [
      {
        id: 'meme-1',
        name: 'Cười ỉa luôn á',
        url: 'https://api.dicebear.com/7.x/fun-emoji/svg?seed=meme-haha&backgroundColor=fef08a',
        keywords: ['haha', 'chet cuoi', 'cuoi ia', 'hai huoc', 'kaka'],
        isAnimated: true,
      },
      {
        id: 'meme-2',
        name: 'Ủa alo là sao',
        url: 'https://api.dicebear.com/7.x/fun-emoji/svg?seed=meme-alo&backgroundColor=fed7aa',
        keywords: ['alo', 'ua alo', 'la sao', 'sao the', 'kho hieu'],
        isAnimated: false,
      },
      {
        id: 'meme-3',
        name: 'U là trời ngạc nhiên',
        url: 'https://api.dicebear.com/7.x/fun-emoji/svg?seed=meme-wow&backgroundColor=bbf7d0',
        keywords: ['u la troi', 'troi oi', 'wow', 'kinh ngac'],
        isAnimated: true,
      },
      {
        id: 'meme-4',
        name: 'Tuyệt đỉnh số 1',
        url: 'https://api.dicebear.com/7.x/fun-emoji/svg?seed=meme-good&backgroundColor=bae6fd',
        keywords: ['dinh', 'so 1', 'tuyet', 'ok', 'chuan'],
        isAnimated: false,
      },
      {
        id: 'meme-5',
        name: 'Khóc một dòng sông',
        url: 'https://api.dicebear.com/7.x/fun-emoji/svg?seed=meme-cry&backgroundColor=ddd6fe',
        keywords: ['huhu', 'khoc', 'dau don', 'tui than', 'buon'],
        isAnimated: true,
      },
      {
        id: 'meme-6',
        name: 'Bất lực không buồn nói',
        url: 'https://api.dicebear.com/7.x/fun-emoji/svg?seed=meme-speechless&backgroundColor=fbcfe8',
        keywords: ['bat luc', 'can loi', 'chao thua', 'chan'],
        isAnimated: false,
      },
    ],
  },
  {
    id: 'celebration-pack',
    name: 'Chúc Mừng & Sinh Nhật',
    author: 'Vibe Creator',
    category: 'Chúc mừng & Lễ Tết',
    avatarUrl: 'https://api.dicebear.com/7.x/bottts/svg?seed=party-cover&backgroundColor=fed7aa',
    description: 'Bánh kem, pháo bông, chúc mừng sinh nhật, tân gia, vinh danh thành công.',
    isInstalled: true,
    stickers: [
      {
        id: 'party-1',
        name: 'Chúc mừng sinh nhật',
        url: 'https://api.dicebear.com/7.x/bottts/svg?seed=party-cake&backgroundColor=fef08a',
        keywords: ['chuc mung sinh nhat', 'sinh nhat', 'hpbd', 'snvv', 'banh kem'],
        isAnimated: true,
      },
      {
        id: 'party-2',
        name: 'Bắn pháo hoa ăn mừng',
        url: 'https://api.dicebear.com/7.x/bottts/svg?seed=party-fireworks&backgroundColor=fbcfe8',
        keywords: ['chuc mung', 'phao hoa', 'an mung', 'thanh cong'],
        isAnimated: true,
      },
      {
        id: 'party-3',
        name: 'Nâng ly dzô dzô',
        url: 'https://api.dicebear.com/7.x/bottts/svg?seed=party-cheers&backgroundColor=bae6fd',
        keywords: ['dzo', 'uong bia', 'nang ly', 'nhau', 'cheers'],
        isAnimated: false,
      },
      {
        id: 'party-4',
        name: 'Tung hoa tán thưởng',
        url: 'https://api.dicebear.com/7.x/bottts/svg?seed=party-flowers&backgroundColor=bbf7d0',
        keywords: ['chuc mung', 'khen', 'hoa', 'tuyet voi'],
        isAnimated: true,
      },
    ],
  },
];

// 3. KHO STICKER STORE MỞ RỘNG (Bộ sưu tập để người dùng khám phá và thêm vào)
export const STORE_STICKER_PACKS: StickerPack[] = [
  ...DEFAULT_STICKER_PACKS,
  {
    id: 'panda-lầy-lội',
    name: 'Gấu Trúc Bựa Lầy',
    author: 'Meme King',
    category: 'Meme & Chibi',
    avatarUrl: 'https://api.dicebear.com/7.x/bottts/svg?seed=panda-pack&backgroundColor=cbd5e1',
    description: 'Bộ sưu tập gấu trúc biểu cảm lầy lội, chuyên trị các cuộc cãi nhau hài hước.',
    isInstalled: false,
    stickers: [
      {
        id: 'panda-1',
        name: 'Chê',
        url: 'https://api.dicebear.com/7.x/bottts/svg?seed=panda-che&backgroundColor=f1f5f9',
        keywords: ['che', 'kem', 'te', 'xau'],
        isAnimated: false,
      },
      {
        id: 'panda-2',
        name: 'Gật đầu lia lịa',
        url: 'https://api.dicebear.com/7.x/bottts/svg?seed=panda-nod&backgroundColor=e2e8f0',
        keywords: ['ok', 'gat dau', 'nhat tri', 'chuan'],
        isAnimated: true,
      },
      {
        id: 'panda-3',
        name: 'Đố anh bắt được em',
        url: 'https://api.dicebear.com/7.x/bottts/svg?seed=panda-run&backgroundColor=cbd5e1',
        keywords: ['chay', 'lac', 'treu', 'bye'],
        isAnimated: true,
      },
    ],
  },
  {
    id: 'love-couple',
    name: 'Tình Yêu Cặp Đôi',
    author: 'Sweet Heart',
    category: 'Tình cảm',
    avatarUrl: 'https://api.dicebear.com/7.x/fun-emoji/svg?seed=couple-pack&backgroundColor=fecdd3',
    description: 'Kho sticker lãng mạn dành cho các cặp đôi nhắn tin mỗi ngày.',
    isInstalled: false,
    stickers: [
      {
        id: 'love-1',
        name: 'Ôm một cái thật chặt',
        url: 'https://api.dicebear.com/7.x/fun-emoji/svg?seed=couple-hug&backgroundColor=ffe4e6',
        keywords: ['om', 'yeu', 'thuong', 'hug'],
        isAnimated: true,
      },
      {
        id: 'love-2',
        name: 'Nhớ em nhiều lắm',
        url: 'https://api.dicebear.com/7.x/fun-emoji/svg?seed=couple-miss&backgroundColor=fecdd3',
        keywords: ['nho', 'miss', 'nho em', 'nho anh'],
        isAnimated: false,
      },
    ],
  },
];

// 4. KHO ẢNH GIF ĐỘNG PHONG PHÚ
export const DEFAULT_GIFS: GifItem[] = [
  {
    id: 'gif-haha-1',
    title: 'Cười ngả nghiêng',
    url: 'https://media.giphy.com/media/10JhviFuU2gWD6/giphy.gif',
    previewUrl: 'https://media.giphy.com/media/10JhviFuU2gWD6/200w.gif',
    category: 'Haha',
  },
  {
    id: 'gif-love-1',
    title: 'Bắn tim bay phấp phới',
    url: 'https://media.giphy.com/media/R6gVNROjZa40PWoGOZ/giphy.gif',
    previewUrl: 'https://media.giphy.com/media/R6gVNROjZa40PWoGOZ/200w.gif',
    category: 'Yêu thương',
  },
  {
    id: 'gif-clap-1',
    title: 'Vỗ tay nhiệt liệt',
    url: 'https://media.giphy.com/media/artj92V8o75VPL7AeQ/giphy.gif',
    previewUrl: 'https://media.giphy.com/media/artj92V8o75VPL7AeQ/200w.gif',
    category: 'Tán thưởng',
  },
  {
    id: 'gif-party-1',
    title: 'Chúc mừng sinh nhật rực rỡ',
    url: 'https://media.giphy.com/media/feqPelMucjY5F3fv2W/giphy.gif',
    previewUrl: 'https://media.giphy.com/media/feqPelMucjY5F3fv2W/200w.gif',
    category: 'Sinh nhật',
  },
  {
    id: 'gif-dance-1',
    title: 'Nhảy múa quẩy nhiệt tình',
    url: 'https://media.giphy.com/media/blSTtZehjAZ8I/giphy.gif',
    previewUrl: 'https://media.giphy.com/media/blSTtZehjAZ8I/200w.gif',
    category: 'Quẩy',
  },
  {
    id: 'gif-bye-1',
    title: 'Vẫy tay tạm biệt',
    url: 'https://media.giphy.com/media/m9eG1qVjvNINAj2CcL/giphy.gif',
    previewUrl: 'https://media.giphy.com/media/m9eG1qVjvNINAj2CcL/200w.gif',
    category: 'Tạm biệt',
  },
];

// 5. TỪ ĐIỂN CẢM XÚC GỢI Ý STICKER TỰ ĐỘNG (Context-Aware Recommendation Dictionary)
export interface EmotionRule {
  keywords: string[];
  suggestedEmojis: string[];
  stickerKeywordMatch: string;
}

export const CONTEXT_EMOTION_RULES: EmotionRule[] = [
  {
    keywords: ['haha', 'hihi', 'kaka', 'cuoi', 'hai', 'vui', 'chet cuoi', 'lol', 'rofl'],
    suggestedEmojis: ['🤣', '😂', '😆', '😄', '😁'],
    stickerKeywordMatch: 'haha',
  },
  {
    keywords: ['yeu', 'thuong', 'nho', 'iu', 'love', 'hon', 'moa', 'crush', 'thich'],
    suggestedEmojis: ['🥰', '😍', '❤️', '💖', '😘'],
    stickerKeywordMatch: 'yeu',
  },
  {
    keywords: ['buon', 'khoc', 'huhu', 'sad', 'tui than', 'dau long', 'that vong', 'chia tay'],
    suggestedEmojis: ['😭', '😢', '🥺', '💔', '😔'],
    stickerKeywordMatch: 'buon',
  },
  {
    keywords: ['chuc mung sinh nhat', 'sinh nhat', 'hpbd', 'snvv', 'banh kem'],
    suggestedEmojis: ['🎂', '🎉', '🥳', '🎁', '🍰'],
    stickerKeywordMatch: 'sinh nhat',
  },
  {
    keywords: ['chao', 'hello', 'hi', 'helo', 'xin chao', 'alo'],
    suggestedEmojis: ['👋', '🙋‍♂️', '✨', '😃', '🤙'],
    stickerKeywordMatch: 'chao',
  },
  {
    keywords: ['ngu ngon', 'g9', 'di ngu', 'sleep', 'ngu day'],
    suggestedEmojis: ['😴', '🌙', '💤', '🛌', '✨'],
    stickerKeywordMatch: 'ngu ngon',
  },
  {
    keywords: ['cam on', 'thank', 'tks', 'biet on', 'cam on nhieu'],
    suggestedEmojis: ['🙏', '💖', '💐', '🤝', '👍'],
    stickerKeywordMatch: 'cam on',
  },
  {
    keywords: ['xin loi', 'sorry', 'ngai', 'so ri', 'bo qua'],
    suggestedEmojis: ['🥺', '🙏', '🙇‍♂️', '😔', '💐'],
    stickerKeywordMatch: 'xin loi',
  },
  {
    keywords: ['dinh', 'so 1', 'tuyet', 'ok', 'chuan', 'gioi', 'dinh cao', 'vip'],
    suggestedEmojis: ['👍', '💯', '🔥', '👑', '👏'],
    stickerKeywordMatch: 'dinh',
  },
  {
    keywords: ['gian', 'tuc', 'buc', 'cau', 'kho chiu', 'dien mau'],
    suggestedEmojis: ['😡', '😠', '🤬', '😤', '👊'],
    stickerKeywordMatch: 'gian',
  },
];
