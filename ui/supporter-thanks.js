/* 100 authored, offline thank-you lines. Columns: en, pt-BR, es, zh-Hans, ja, ru. */
(() => {
    "use strict";
    const lines = [
    [
        "My tail voted for you. Unanimously.",
        "Meu rabo votou em você. Por unanimidade.",
        "Mi cola votó por ti. Por unanimidad.",
        "我的尾巴全票支持你。",
        "しっぽの投票は全会一致で君に決定。",
        "Мой хвост проголосовал за вас. Единогласно."
    ],
    [
        "You just earned a very enthusiastic sniff.",
        "Você acaba de ganhar uma cheirada muito animada.",
        "Te has ganado un olfateo muy entusiasta.",
        "你赢得了一次热情的嗅嗅。",
        "とびきり熱心なくんくんを贈るよ。",
        "Вам полагается очень восторженное обнюхивание."
    ],
    [
        "I saved you a spot beside my nap.",
        "Guardei um lugar para você ao lado da minha soneca.",
        "Te guardé un sitio junto a mi siesta.",
        "给你留了个挨着我午睡的位置。",
        "お昼寝の隣の席、空けておいたよ。",
        "Я оставил вам место рядом с моим дневным сном."
    ],
    [
        "Your support made my ears perk up.",
        "Seu apoio até levantou minhas orelhas.",
        "Tu apoyo hasta me levantó las orejas.",
        "你的支持让我耳朵都竖起来了。",
        "応援で耳がぴんと立っちゃった。",
        "От вашей поддержки у меня даже уши поднялись."
    ],
    [
        "Marcos said thanks. I added tail wags.",
        "O Marcos agradeceu. Eu acrescentei umas abanadas.",
        "Marcos dio las gracias. Yo añadí unos meneos de cola.",
        "Marcos 说谢谢，我补上了摇尾巴。",
        "Marcos のありがとうに、しっぽのふりふりを追加。",
        "Маркос сказал спасибо. Я добавил виляние хвостом."
    ],
    [
        "You smell like excellent decisions.",
        "Você tem cheiro de boas decisões.",
        "Hueles a buenas decisiones.",
        "你闻起来像做了个好决定。",
        "いい判断をする人のにおいがする。",
        "От вас пахнет отличными решениями."
    ],
    [
        "I'd share my favorite blanket. Briefly.",
        "Eu dividiria minha coberta favorita. Por pouco tempo.",
        "Compartiría mi manta favorita. Un ratito.",
        "愿意和你分享最爱的毯子，就一小会儿。",
        "お気に入りの毛布、少しだけなら貸すよ。",
        "Я бы поделился любимым пледом. Ненадолго."
    ],
    [
        "That deserves a stretch and a thank-you.",
        "Isso merece uma espreguiçada e um obrigado.",
        "Eso merece un estirón y unas gracias.",
        "值得伸个懒腰，再说声谢谢。",
        "伸びをひとつ。それから、ありがとう。",
        "Это заслуживает потягушек и благодарности."
    ],
    [
        "A good human. I can spot those.",
        "Humano dos bons. Eu reconheço de longe.",
        "Una buena persona. Las reconozco de lejos.",
        "是个好人，我一眼就认得。",
        "いい人だね。僕には分かる。",
        "Хорошего человека я вижу сразу."
    ],
    [
        "You helped the project. I supervised the helping.",
        "Você ajudou o projeto. Eu fiscalizei a ajuda.",
        "Ayudaste al proyecto. Yo supervisé la ayuda.",
        "你帮了项目，我负责监督这份帮助。",
        "君がプロジェクトを応援。僕は応援を監督。",
        "Вы помогли проекту. Я проконтролировал помощь."
    ],
    [
        "I'd fetch a thank-you, but this is quicker.",
        "Eu iria buscar um obrigado, mas assim é mais rápido.",
        "Iría a buscar unas gracias, pero esto es más rápido.",
        "本想叼个谢谢回来，这样更快。",
        "ありがとうを取ってきてもいいけど、こっちが早いね。",
        "Я бы принёс вам спасибо, но так быстрее."
    ],
    [
        "My glasses confirm it: excellent human.",
        "Meus óculos confirmam: excelente humano.",
        "Mis gafas lo confirman: excelente persona.",
        "眼镜确认了，你是个优秀的人类。",
        "眼鏡でも確認。すばらしい人間だ。",
        "Очки подтверждают: отличный человек."
    ],
    [
        "You got a thank-you without even ringing the doorbell.",
        "Você ganhou um obrigado sem nem tocar a campainha.",
        "Te ganaste unas gracias sin tocar el timbre.",
        "没按门铃就收到了我的感谢。",
        "チャイムを鳴らさずに、ありがとうを獲得。",
        "Вы получили спасибо, даже не позвонив в дверь."
    ],
    [
        "I paused my nap for this. That's a big deal.",
        "Pausei minha soneca para isso. É coisa séria.",
        "Pausé mi siesta por esto. Es importante.",
        "我为此暂停了午睡，这可是大事。",
        "お昼寝を中断したんだ。これは特別だよ。",
        "Я ради этого прервал сон. Это серьёзно."
    ],
    [
        "Consider yourself warmly sniff-approved.",
        "Considere-se aprovado com uma boa cheirada.",
        "Considérate aprobado con un buen olfateo.",
        "经过亲切嗅嗅，你通过了。",
        "くんくん審査、あたたかく合格です。",
        "Считайте, что вы одобрены после тёплого обнюхивания."
    ],
    [
        "If gratitude were fur, you'd need a lint roller.",
        "Se gratidão fosse pelo, você ia precisar de um rolinho.",
        "Si la gratitud fuera pelo, necesitarías un rodillo.",
        "要是感谢是毛，你得准备粘毛滚筒。",
        "感謝が毛だったら、コロコロが必要だね。",
        "Будь благодарность шерстью, вам понадобился бы липкий ролик."
    ],
    [
        "Thanks for helping my human build things.",
        "Obrigado por ajudar meu humano a construir as coisas.",
        "Gracias por ayudar a mi humano a crear cosas.",
        "谢谢你帮我的人类做东西。",
        "僕の人間のものづくりを応援してくれてありがとう。",
        "Спасибо, что помогаете моему человеку создавать новое."
    ],
    [
        "I wagged so much I nearly rebooted.",
        "Abanei tanto que quase reiniciei.",
        "Moví tanto la cola que casi me reinicio.",
        "尾巴摇太猛，差点重启了。",
        "しっぽを振りすぎて再起動しそうだった。",
        "Я так вилял хвостом, что чуть не перезагрузился."
    ],
    [
        "Your name passed the nose test.",
        "Seu nome passou no teste do focinho.",
        "Tu nombre pasó la prueba del hocico.",
        "你的名字通过了鼻子测试。",
        "君の名前、鼻チェック合格。",
        "Ваше имя прошло проверку носом."
    ],
    [
        "One thank-you, with extra enthusiasm.",
        "Um obrigado, com entusiasmo extra.",
        "Unas gracias, con entusiasmo extra.",
        "一份谢谢，加倍热情。",
        "ありがとう、元気増しで。",
        "Одно спасибо, с добавкой восторга."
    ],
    [
        "I'd bring you a toy. It's a little damp.",
        "Eu levaria um brinquedo. Ele está meio babado.",
        "Te traería un juguete. Está un poco baboseado.",
        "想给你叼个玩具，就是有点湿。",
        "おもちゃを持ってくるよ。ちょっと湿ってるけど。",
        "Я бы принёс игрушку. Она слегка обслюнявлена."
    ],
    [
        "You deserve the sunny spot by the window.",
        "Você merece o lugarzinho de sol na janela.",
        "Te mereces el rincón de sol junto a la ventana.",
        "窗边晒太阳的位置让给你。",
        "窓辺の日なた席、君にどうぞ。",
        "Вы заслужили солнечное место у окна."
    ],
    [
        "I asked the stars. They like you too.",
        "Perguntei às estrelas. Elas também gostaram de você.",
        "Pregunté a las estrellas. También les caes bien.",
        "问过星星了，它们也喜欢你。",
        "星にも聞いたよ。星も君が好きだって。",
        "Я спросил звёзды. Вы им тоже нравитесь."
    ],
    [
        "This is my grateful face. The glasses stay on.",
        "Esta é minha cara de agradecido. Os óculos ficam.",
        "Esta es mi cara de agradecido. Las gafas se quedan.",
        "这是我的感谢脸，眼镜不摘。",
        "これが感謝の顔。眼鏡はかけたままで。",
        "Это моё благодарное лицо. Очки не снимаю."
    ],
    [
        "You helped. My tail handled the celebration.",
        "Você ajudou. Meu rabo cuidou da comemoração.",
        "Tú ayudaste. Mi cola se encargó de celebrar.",
        "你负责支持，尾巴负责庆祝。",
        "君が応援、しっぽがお祝い担当。",
        "Вы помогли. Празднование взял на себя мой хвост."
    ],
    [
        "I'd give you a high five. Mine has fur.",
        "Eu te daria um toca aqui. O meu tem pelo.",
        "Te chocaría esos cinco. Los míos tienen pelo.",
        "想跟你击掌，我的掌有毛。",
        "ハイタッチしよう。僕のは毛があるけど。",
        "Дал бы вам пять. Моя пятерня в шерсти."
    ],
    [
        "A little support goes far on little legs.",
        "Uma ajuda vai longe nessas perninhas curtas.",
        "Una ayuda llega lejos con estas patitas cortas.",
        "小小支持，让小短腿走得更远。",
        "小さな応援で、短い足も遠くへ行ける。",
        "С поддержкой даже короткие лапки идут далеко."
    ],
    [
        "You made my day. The nap was already booked.",
        "Você fez meu dia. A soneca já estava agendada.",
        "Me alegraste el día. La siesta ya estaba reservada.",
        "你让我今天很开心，午睡早就预约好了。",
        "いい一日になったよ。昼寝の予約はそのままね。",
        "Вы сделали мой день лучше. Сон уже был запланирован."
    ],
    [
        "Thank you. That's the important part. Woof is the rest.",
        "Obrigado. Essa é a parte importante. O resto é au.",
        "Gracias. Eso es lo importante. Lo demás es guau.",
        "谢谢，这是重点，剩下的都是汪。",
        "ありがとう。大事なのはそこ。あとはワン。",
        "Спасибо — это главное. Остальное — гав."
    ],
    [
        "Your kindness has been thoroughly sniffed.",
        "Sua gentileza foi devidamente farejada.",
        "Tu amabilidad ha sido debidamente olfateada.",
        "你的好意已经被仔细嗅过了。",
        "君の優しさ、しっかりくんくんしたよ。",
        "Ваша доброта тщательно обнюхана."
    ],
    [
        "I'd write a thank-you note, but I have paws.",
        "Eu escreveria um bilhete, mas tenho patas.",
        "Escribiría una nota de agradecimiento, pero tengo patas.",
        "本想写张感谢卡，可我只有爪子。",
        "お礼の手紙を書きたいけど、この手は肉球なんだ。",
        "Я бы написал благодарность, но у меня лапки."
    ],
    [
        "You can sit with us. I'll take most of the chair.",
        "Pode sentar com a gente. Eu fico com quase toda a cadeira.",
        "Puedes sentarte con nosotros. Yo ocupo casi toda la silla.",
        "来和我们坐吧，椅子大部分归我。",
        "一緒に座ろう。椅子の大半は僕だけど。",
        "Садитесь с нами. Почти весь стул займусь я."
    ],
    [
        "That support earned a very dignified happy dance.",
        "Esse apoio ganhou uma dancinha muito respeitável.",
        "Ese apoyo se ganó un bailecito muy digno.",
        "这份支持值得跳一支非常庄重的开心舞。",
        "応援のお礼に、とても上品な喜びのダンス。",
        "За такую поддержку полагается очень солидный танец радости."
    ],
    [
        "Even my imaginary space tail is wagging.",
        "Até meu rabo espacial imaginário está abanando.",
        "Hasta mi cola espacial imaginaria se mueve.",
        "连我想象中的太空尾巴都摇起来了。",
        "想像の宇宙しっぽまで振れちゃう。",
        "Даже мой воображаемый космический хвост виляет."
    ],
    [
        "I put your thank-you ahead of my nap.",
        "Coloquei seu obrigado na frente da minha soneca.",
        "Puse tus gracias antes de mi siesta.",
        "你的感谢排在午睡前面。",
        "君へのありがとうを、お昼寝より先にしたよ。",
        "Спасибо вам поставил раньше своего сна."
    ],
    [
        "You brought support. I brought the eyebrows.",
        "Você trouxe apoio. Eu trouxe as sobrancelhas.",
        "Tú trajiste apoyo. Yo traje las cejas.",
        "你带来支持，我带来眉毛。",
        "君は応援、僕はこの眉毛を持ってきた。",
        "Вы принесли поддержку. Я — выразительные брови."
    ],
    [
        "This galaxy just got a better neighbor.",
        "Essa galáxia acabou de ganhar um vizinho dos bons.",
        "Esta galaxia acaba de ganar un buen vecino.",
        "星系刚迎来一位好邻居。",
        "この銀河に、いいご近所さんが増えた。",
        "У этой галактики появился хороший сосед."
    ],
    [
        "You're welcome near my favorite blanket.",
        "Você tem passe livre perto da minha coberta favorita.",
        "Tienes pase libre cerca de mi manta favorita.",
        "欢迎靠近我最爱的毯子。",
        "お気に入りの毛布の近く、君なら歓迎。",
        "Вам можно рядом с моим любимым пледом."
    ],
    [
        "Thanks for believing in a project named after me.",
        "Obrigado por acreditar num projeto com meu nome.",
        "Gracias por creer en un proyecto con mi nombre.",
        "谢谢你相信这个用我名字命名的项目。",
        "僕の名前のプロジェクトを信じてくれてありがとう。",
        "Спасибо за веру в проект с моим именем."
    ],
    [
        "I tried to keep calm. My tail disagreed.",
        "Tentei manter a pose. Meu rabo discordou.",
        "Intenté mantener la compostura. Mi cola no quiso.",
        "本想保持淡定，尾巴不同意。",
        "落ち着こうとしたけど、しっぽは反対だった。",
        "Я пытался сохранять вид. Хвост был против."
    ],
    [
        "I'd trade one suspicious glance for a thank-you.",
        "Troco um olhar de julgamento por um obrigado.",
        "Cambio una mirada de juicio por unas gracias.",
        "用一个审视的眼神换一句谢谢。",
        "いつものじと目を、ありがとうに交換。",
        "Меняю один осуждающий взгляд на спасибо."
    ],
    [
        "Your support is worth interrupting a sunbeam.",
        "Seu apoio vale interromper um banho de sol.",
        "Tu apoyo merece interrumpir un baño de sol.",
        "为了你的支持，晒太阳也可以暂停。",
        "君の応援なら、ひなたぼっこを中断してもいい。",
        "Ради вашей поддержки стоит прервать солнечную ванну."
    ],
    [
        "I've reserved a grateful head tilt for you.",
        "Reservei uma inclinada de cabeça agradecida para você.",
        "Te reservé una inclinación de cabeza agradecida.",
        "为你预留了一个感谢的歪头。",
        "君のために感謝の首かしげを用意したよ。",
        "Для вас припасён благодарный наклон головы."
    ],
    [
        "You help Marcos build. I remind him to stand up.",
        "Você ajuda o Marcos a criar. Eu lembro ele de levantar.",
        "Ayudas a Marcos a crear. Yo le recuerdo que se levante.",
        "你帮 Marcos 开发，我提醒他起来活动。",
        "君が Marcos の開発を応援。僕は立ち上がるよう促す。",
        "Вы помогаете Маркосу создавать. Я напоминаю ему встать."
    ],
    [
        "Thank you from the bottom of my very fluffy chest.",
        "Obrigado do fundo do meu peito bem peludo.",
        "Gracias desde el fondo de mi pecho peludo.",
        "从我毛茸茸的胸口深处说声谢谢。",
        "もふもふの胸の底から、ありがとう。",
        "Спасибо от всей моей пушистой груди."
    ],
    [
        "I almost shared a biscuit. Almost.",
        "Quase dividi um biscoito. Quase.",
        "Casi compartí una galleta. Casi.",
        "差点就分你一块饼干，差点。",
        "ビスケットを分けかけたよ。かけただけ。",
        "Я почти поделился печеньем. Почти."
    ],
    [
        "Your name got a little star and a big sniff.",
        "Seu nome ganhou uma estrelinha e uma bela cheirada.",
        "Tu nombre ganó una estrellita y un buen olfateo.",
        "你的名字得到一颗小星星和一次大嗅嗅。",
        "君の名前に、小さな星と大きなくんくん。",
        "Вашему имени — маленькая звезда и большое обнюхивание."
    ],
    [
        "You made the supervisor smile. That's me, by the way.",
        "Você fez o fiscal sorrir. O fiscal sou eu, aliás.",
        "Hiciste sonreír al supervisor. El supervisor soy yo.",
        "你让监督员笑了，监督员就是我。",
        "監督を笑顔にしたね。監督は僕だよ。",
        "Вы заставили надзирателя улыбнуться. Надзиратель — это я."
    ],
    [
        "A good reason to leave the comfy cushion.",
        "Um bom motivo para sair da almofada confortável.",
        "Una buena razón para dejar el cojín cómodo.",
        "这是离开舒服垫子的好理由。",
        "ふかふかのクッションを離れる、いい理由だね。",
        "Хороший повод покинуть удобную подушку."
    ],
    [
        "If I had pockets, I'd keep your thank-you in one.",
        "Se eu tivesse bolsos, guardava seu obrigado num deles.",
        "Si tuviera bolsillos, guardaría tus gracias en uno.",
        "要是有口袋，我会把给你的谢谢放进去。",
        "ポケットがあったら、君へのありがとうを入れておくよ。",
        "Были бы у меня карманы, хранил бы ваше спасибо в одном."
    ],
    [
        "You get the friendly version of my serious face.",
        "Você ganhou a versão simpática da minha cara séria.",
        "Te tocó la versión amable de mi cara seria.",
        "给你看我严肃脸的友好版本。",
        "真顔の、親しみやすいバージョンをどうぞ。",
        "Вам досталась дружелюбная версия моего строгого лица."
    ],
    [
        "The thank-you is yours. The slipper is mine.",
        "O obrigado é seu. O chinelo é meu.",
        "Las gracias son tuyas. La zapatilla es mía.",
        "谢谢归你，拖鞋归我。",
        "ありがとうは君に。スリッパは僕に。",
        "Спасибо — ваше. Тапок — мой."
    ],
    [
        "You're helping a small project take bigger walks.",
        "Você ajuda um projeto pequeno a dar passeios maiores.",
        "Ayudas a un proyecto pequeño a dar paseos más largos.",
        "你帮这个小项目走上更远的散步路。",
        "小さなプロジェクトが、もっと遠くへお散歩できるね。",
        "Вы помогаете маленькому проекту гулять всё дальше."
    ],
    [
        "I thanked you with my face. My tail sent a copy.",
        "Agradeci com a cara. Meu rabo mandou uma cópia.",
        "Te di las gracias con la cara. Mi cola envió una copia.",
        "我用表情道谢，尾巴发了份副本。",
        "顔でお礼を伝えたよ。しっぽからもコピーを送った。",
        "Я поблагодарил лицом. Хвост отправил копию."
    ],
    [
        "Your support has my full attention. For a whole moment.",
        "Seu apoio tem minha atenção total. Por um momento inteiro.",
        "Tu apoyo tiene toda mi atención. Durante un momento entero.",
        "你的支持获得了我全部注意力，整整一会儿。",
        "君の応援に全力で注目。まるまる一瞬ね。",
        "Ваша поддержка получила всё моё внимание. На целый миг."
    ],
    [
        "This is the part where I'd lean against your leg.",
        "Essa é a parte em que eu encostaria na sua perna.",
        "Aquí es cuando me apoyaría en tu pierna.",
        "这时候我本该靠在你腿上。",
        "ここで君の足に、そっと寄りかかるところだね。",
        "Сейчас я бы прислонился к вашей ноге."
    ],
    [
        "My little paws approve of your big kindness.",
        "Minhas patinhas aprovam sua grande gentileza.",
        "Mis patitas aprueban tu gran amabilidad.",
        "小爪子批准了你的大善意。",
        "小さな肉球が、君の大きな優しさを承認。",
        "Мои маленькие лапки одобряют вашу большую доброту."
    ],
    [
        "You deserve a thank-you with both ears up.",
        "Você merece um obrigado com as duas orelhas em pé.",
        "Mereces unas gracias con las dos orejas arriba.",
        "值得双耳竖起来说谢谢。",
        "両耳をぴんと立てて、ありがとう。",
        "Вы заслужили спасибо с обоими ушами торчком."
    ],
    [
        "I checked the code. Then I checked for snacks. Thanks.",
        "Conferi o código. Depois procurei petiscos. Obrigado.",
        "Revisé el código. Luego busqué premios. Gracias.",
        "检查了代码，又找了零食，谢谢。",
        "コードを確認。それからおやつを確認。ありがとう。",
        "Проверил код. Потом поискал вкусняшки. Спасибо."
    ],
    [
        "I'd name a comet after you, but I might fetch it.",
        "Eu daria seu nome a um cometa, mas talvez fosse buscar.",
        "Le pondría tu nombre a un cometa, pero quizá vaya a buscarlo.",
        "想用你的名字给彗星命名，可我可能会去叼回来。",
        "君の名前を彗星につけたいけど、取ってきちゃうかも。",
        "Я бы назвал комету в вашу честь, но могу побежать за ней."
    ],
    [
        "You made the galaxy feel a bit more like home.",
        "Você deixou essa galáxia com mais cara de casa.",
        "Hiciste que esta galaxia se sintiera más como casa.",
        "你让这片星系更像家了。",
        "この銀河が、少し家みたいに感じるね。",
        "С вами эта галактика стала чуть больше похожа на дом."
    ],
    [
        "My tail has prepared a short presentation.",
        "Meu rabo preparou uma apresentação curta.",
        "Mi cola preparó una breve presentación.",
        "尾巴准备了一个简短的演示。",
        "しっぽが短いプレゼンを用意したよ。",
        "Мой хвост подготовил короткую презентацию."
    ],
    [
        "Thank you. I practiced saying it without barking.",
        "Obrigado. Treinei para falar sem latir.",
        "Gracias. Practiqué decirlo sin ladrar.",
        "谢谢，我练过不汪汪地说。",
        "ありがとう。吠えずに言う練習をしたんだ。",
        "Спасибо. Я тренировался говорить это без лая."
    ],
    [
        "You helped turn a thought into another day of building.",
        "Você ajudou uma ideia a ganhar mais um dia de trabalho.",
        "Ayudaste a que una idea tuviera otro día de trabajo.",
        "你让一个想法又多了一天成长的时间。",
        "ひとつの思いつきに、もう一日作る時間をくれたね。",
        "Вы подарили идее ещё один день работы."
    ],
    [
        "I'm grateful enough to move off the keyboard.",
        "Estou tão agradecido que até saio de cima do teclado.",
        "Estoy tan agradecido que hasta me quito del teclado.",
        "感激到愿意从键盘上挪开了。",
        "感謝してるから、キーボードの上からどくよ。",
        "Я так благодарен, что даже уйду с клавиатуры."
    ],
    [
        "A little tail wag just crossed the galaxy for you.",
        "Uma abanadinha acabou de cruzar a galáxia por você.",
        "Un meneo de cola acaba de cruzar la galaxia por ti.",
        "一小下摇尾巴刚为你穿过了星系。",
        "君のためのしっぽふりが、銀河を渡ったよ。",
        "Ради вас маленькое виляние хвостом пересекло галактику."
    ],
    [
        "You're the sort of human I'd follow into the kitchen.",
        "Você é do tipo de humano que eu seguiria até a cozinha.",
        "Eres de esas personas que seguiría hasta la cocina.",
        "你是那种我愿意跟进厨房的人。",
        "君ならキッチンまでついていきたいな。",
        "За таким человеком, как вы, я бы пошёл на кухню."
    ],
    [
        "I'd offer a paw, but I'm using it to supervise.",
        "Eu ofereceria a pata, mas estou usando para fiscalizar.",
        "Te daría la pata, pero la uso para supervisar.",
        "想递只爪子，可它正忙着监督。",
        "お手をしたいけど、今は監督に使ってるんだ。",
        "Я бы подал лапу, но она занята надзором."
    ],
    [
        "You made me forget to look unimpressed.",
        "Você me fez esquecer de bancar o indiferente.",
        "Me hiciste olvidar mi cara de indiferencia.",
        "你让我忘了摆出不以为然的脸。",
        "つまらなそうな顔をするの、忘れちゃった。",
        "Вы заставили меня забыть про равнодушный вид."
    ],
    [
        "This thank-you comes with imaginary paw prints.",
        "Esse obrigado vem com pegadinhas imaginárias.",
        "Estas gracias vienen con huellas imaginarias.",
        "这份谢谢附赠想象中的爪印。",
        "このありがとうには、想像の足あと付き。",
        "К этому спасибо прилагаются воображаемые следы лап."
    ],
    [
        "Good human detected. Happy dog activated.",
        "Humano dos bons detectado. Cachorro feliz ativado.",
        "Buena persona detectada. Perro feliz activado.",
        "发现好人类，开心狗狗已启动。",
        "いい人間を検知。うれしい犬モード起動。",
        "Обнаружен хороший человек. Счастливый пёс активирован."
    ],
    [
        "I told Marcos about you. He can stop coding to smile.",
        "Contei de você para o Marcos. Ele pode parar de programar para sorrir.",
        "Le hablé de ti a Marcos. Puede parar de programar para sonreír.",
        "我告诉了 Marcos，他可以停下代码笑一笑。",
        "Marcos に君のことを伝えたよ。コードを止めて笑えるね。",
        "Рассказал о вас Маркосу. Может оторваться от кода и улыбнуться."
    ],
    [
        "Your support is a good excuse for a victory stretch.",
        "Seu apoio é uma boa desculpa para uma espreguiçada de vitória.",
        "Tu apoyo es una buena excusa para un estirón de victoria.",
        "你的支持是伸个胜利懒腰的好理由。",
        "君の応援を口実に、勝利の伸びをひとつ。",
        "Ваша поддержка — хороший повод для победных потягушек."
    ],
    [
        "I made room for you in my very selective pack.",
        "Abri uma vaga para você na minha turma bem exigente.",
        "Te hice sitio en mi manada muy selectiva.",
        "我这挑剔的小队给你留了位置。",
        "かなり選り好みする僕の仲間に、君の席を用意したよ。",
        "Я нашёл для вас место в своей очень разборчивой стае."
    ],
    [
        "Thanks for helping the human behind my glasses.",
        "Obrigado por ajudar o humano por trás dos meus óculos.",
        "Gracias por ayudar al humano detrás de mis gafas.",
        "谢谢你帮助我这副眼镜背后的人类。",
        "この眼鏡の向こうにいる人間を応援してくれてありがとう。",
        "Спасибо, что помогаете человеку за моими очками."
    ],
    [
        "I would howl your name. The neighbors prefer this.",
        "Eu uivaria seu nome. Os vizinhos preferem assim.",
        "Aullaría tu nombre. Los vecinos prefieren esto.",
        "本想把你的名字嗷出来，邻居更喜欢这样。",
        "名前を遠吠えしたいけど、ご近所さんはこっちがいいって。",
        "Я бы провыл ваше имя. Но соседи предпочитают так."
    ],
    [
        "You earned my rarest expression: visibly impressed.",
        "Você ganhou minha expressão mais rara: impressionado.",
        "Te ganaste mi expresión más rara: impresionado.",
        "你解锁了我最罕见的表情：佩服。",
        "珍しい表情をどうぞ。感心してる顔だよ。",
        "Вы заслужили моё редчайшее выражение: впечатлён."
    ],
    [
        "One small click, one very happy little dog.",
        "Um clique pequeno, um cachorrinho muito feliz.",
        "Un pequeño clic, un perrito muy feliz.",
        "小小一点，一只超开心的小狗。",
        "小さなクリックで、小さな犬は大喜び。",
        "Один маленький клик — и один очень счастливый пёс."
    ],
    [
        "My thank-you has no leash. It goes everywhere.",
        "Meu obrigado não tem coleira. Vai para todo lado.",
        "Mis gracias no llevan correa. Van a todas partes.",
        "我的感谢不拴绳，到处跑。",
        "ありがとうはリードなし。どこまでも行くよ。",
        "Моё спасибо без поводка. Гуляет повсюду."
    ],
    [
        "You made this corner of the internet a little warmer.",
        "Você deixou esse canto da internet um pouco mais acolhedor.",
        "Hiciste más cálido este rincón de internet.",
        "你让互联网的这一角暖和了一点。",
        "ネットのこの片隅が、少しあたたかくなったね。",
        "Вы сделали этот уголок интернета чуть теплее."
    ],
    [
        "I'd leave a thank-you on your doorstep. A clean one.",
        "Eu deixaria um obrigado na sua porta. Um limpinho.",
        "Dejaría unas gracias en tu puerta. Bien limpias.",
        "想在你门口放一份谢谢，干净的那种。",
        "玄関にありがとうを置いておくよ。きれいなやつ。",
        "Я бы оставил спасибо у вашей двери. Чистенькое."
    ],
    [
        "You helped the code. I handled morale.",
        "Você ajudou o código. Eu cuidei da animação da equipe.",
        "Ayudaste al código. Yo cuidé el ánimo del equipo.",
        "你帮代码，我负责鼓舞士气。",
        "君はコードを支援。僕は士気を担当。",
        "Вы помогли коду. Я занялся боевым духом."
    ],
    [
        "You're worth more than one polite tail wag.",
        "Você merece mais que uma abanada educada.",
        "Mereces más de un meneo de cola educado.",
        "你值得不止一次礼貌摇尾巴。",
        "礼儀正しく一回、じゃ足りないね。",
        "Вы заслуживаете больше одного вежливого виляния хвостом."
    ],
    [
        "I sniffed around. Your support checks out.",
        "Farejei por aí. Seu apoio está aprovadíssimo.",
        "Olfateé por ahí. Tu apoyo está aprobadísimo.",
        "到处嗅了一圈，你的支持完全通过。",
        "くんくん調べたよ。君の応援はばっちり。",
        "Я всё обнюхал. Ваша поддержка одобрена."
    ],
    [
        "I'd share my sunbeam, but let's take turns.",
        "Eu divido meu raio de sol, mas vamos revezar.",
        "Comparto mi rayo de sol, pero por turnos.",
        "阳光可以分你，不过咱们轮流。",
        "日なたは分けるけど、交代でね。",
        "Поделюсь солнечным лучом, но по очереди."
    ],
    [
        "You make the next small step feel possible.",
        "Você faz o próximo passinho parecer possível.",
        "Haces que el próximo pasito parezca posible.",
        "你让下一个小步变得可行。",
        "次の小さな一歩が、踏み出せそうだよ。",
        "С вами следующий маленький шаг кажется возможным."
    ],
    [
        "My serious glasses are hiding a happy dog.",
        "Meus óculos sérios estão escondendo um cachorro feliz.",
        "Mis gafas serias esconden un perro feliz.",
        "严肃的眼镜藏不住开心的狗。",
        "まじめな眼鏡の奥で、犬は喜んでるよ。",
        "За серьёзными очками прячется счастливый пёс."
    ],
    [
        "A thank-you so warm I'd nap beside it.",
        "Um obrigado tão quentinho que eu dormiria do lado.",
        "Unas gracias tan cálidas que dormiría a su lado.",
        "这份谢谢暖得让我想睡在旁边。",
        "あったかいありがとう。その隣で昼寝したいな。",
        "Такое тёплое спасибо, что я бы рядом уснул."
    ],
    [
        "You didn't have to help. That makes it even nicer.",
        "Você não precisava ajudar. Isso deixa tudo ainda mais legal.",
        "No tenías que ayudar. Eso lo hace aún más bonito.",
        "你本来不必帮忙，所以这份支持更暖心。",
        "応援は義務じゃない。だから、なおさらうれしい。",
        "Вы не обязаны были помогать. Оттого это ещё приятнее."
    ],
    [
        "I brought a thank-you and absolutely no personal space.",
        "Trouxe um obrigado e nenhum respeito pelo espaço pessoal.",
        "Traje unas gracias y ningún respeto por el espacio personal.",
        "带来了谢谢，以及零距离感。",
        "ありがとうと、距離感ゼロを持ってきたよ。",
        "Принёс спасибо и полное отсутствие личных границ."
    ],
    [
        "Your support got the deluxe head tilt.",
        "Seu apoio ganhou a inclinada de cabeça de luxo.",
        "Tu apoyo ganó la inclinación de cabeza de lujo.",
        "你的支持赢得了豪华歪头服务。",
        "君の応援には、豪華版の首かしげを。",
        "За вашу поддержку — наклон головы класса люкс."
    ],
    [
        "I'd thank you twice, but my tail already did.",
        "Eu agradeceria duas vezes, mas meu rabo já fez isso.",
        "Te daría las gracias dos veces, pero mi cola ya lo hizo.",
        "本想谢两次，可尾巴已经谢过了。",
        "二回お礼を言いたいけど、しっぽがもう言ったね。",
        "Поблагодарил бы дважды, но хвост уже успел."
    ],
    [
        "You helped keep a good idea on its feet. All four.",
        "Você ajudou uma boa ideia a ficar de pé. Nas quatro patas.",
        "Ayudaste a una buena idea a seguir en pie. En las cuatro patas.",
        "你帮好点子站稳了，四只脚都稳了。",
        "いいアイデアが立っていられるね。四本足で。",
        "Вы помогли хорошей идее устоять. На всех четырёх лапах."
    ],
    [
        "Thanks for making room for this little project.",
        "Obrigado por abrir espaço para esse pequeno projeto.",
        "Gracias por hacer sitio a este pequeño proyecto.",
        "谢谢你为这个小项目留出空间。",
        "この小さなプロジェクトに場所をくれてありがとう。",
        "Спасибо, что нашли место для этого маленького проекта."
    ],
    [
        "I tried counting my thanks. Ran out of paws.",
        "Tentei contar meus obrigados. Faltaram patas.",
        "Intenté contar mis gracias. Me faltaron patas.",
        "数了一下有多少谢谢，爪子不够用了。",
        "ありがとうを数えたら、足が足りなくなった。",
        "Пытался сосчитать свои спасибо. Лап не хватило."
    ],
    [
        "I'd guard your thank-you like my favorite toy.",
        "Eu guardaria seu obrigado como meu brinquedo favorito.",
        "Cuidaría tus gracias como mi juguete favorito.",
        "会像护着最爱的玩具那样护着这份谢谢。",
        "お気に入りのおもちゃみたいに、ありがとうを守るよ。",
        "Я бы охранял ваше спасибо как любимую игрушку."
    ],
    [
        "You made a small dog feel extremely important.",
        "Você fez um cachorro pequeno se sentir importantíssimo.",
        "Hiciste que un perro pequeño se sintiera importantísimo.",
        "你让小狗觉得自己特别重要。",
        "小さな犬が、とても大事にされた気分だよ。",
        "Вы дали маленькому псу почувствовать себя очень важным."
    ],
    [
        "The human handles the code. I deliver this thank-you.",
        "O humano cuida do código. Eu entrego este obrigado.",
        "El humano cuida el código. Yo entrego estas gracias.",
        "人类负责代码，我负责送达谢谢。",
        "人間はコード担当。僕はこのありがとうのお届け係。",
        "Человек занимается кодом. Я доставляю это спасибо."
    ],
    [
        "I saved the loud bark. You got the happy look.",
        "Guardei o latido alto. Você ganhou o olhar feliz.",
        "Guardé el ladrido fuerte. Te tocó la mirada feliz.",
        "大声的汪先收着，开心眼神送给你。",
        "大きなワンはしまって、うれしい顔を贈るよ。",
        "Громкий лай приберёг. Вам достался счастливый взгляд."
    ],
    [
        "You've made this dog very proud of his human's project.",
        "Você deixou este cachorro muito orgulhoso do projeto do humano.",
        "Hiciste que este perro se sintiera orgulloso del proyecto de su humano.",
        "你让这只狗为人类的项目感到很骄傲。",
        "人間のプロジェクトが、犬として誇らしいよ。",
        "Вы заставили этого пса гордиться проектом своего человека."
    ]
];
    window.TODDY_SUPPORTER_THANKS = lines.map(([english]) => english);
    for (const [english, ...translations] of lines) window.TODDY_TRANSLATIONS[english] = translations;
})();
