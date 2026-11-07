/* 100 editorially reviewed, offline thank-you lines. Columns: en, pt-BR, es, zh-Hans, ja, ru. */
(() => {
    "use strict";
    const lines = [
    [
        "Your support made my day. My tail is taking the credit.",
        "Seu apoio fez meu dia. Meu rabo está levando o crédito.",
        "Tu apoyo me alegró el día. Mi cola se está llevando el mérito.",
        "你的支持让我很开心，尾巴却抢着邀功。",
        "君の応援でいい一日になったよ。しっぽは自分の手柄だと思ってる。",
        "Ваша поддержка сделала мой день лучше. Хвост приписывает это себе."
    ],
    [
        "That was kind of you. I'm trying to say thanks without jumping up.",
        "Que carinho o seu. Estou tentando agradecer sem pular.",
        "Qué detalle tan bonito. Intento darte las gracias sin saltar.",
        "你真好，我正努力不跳起来道谢。",
        "優しいね。飛びつかずにありがとうを言おうとしてるよ。",
        "Как это мило с вашей стороны. Стараюсь благодарить, не подпрыгивая."
    ],
    [
        "I had my serious face ready. Your support brought out the smile.",
        "Eu estava pronto para fazer cara séria. Seu apoio me fez sorrir.",
        "Tenía preparada mi cara seria. Tu apoyo me sacó una sonrisa.",
        "严肃脸都准备好了，你的支持却让我笑了。",
        "まじめな顔を用意してたのに、応援で笑顔になっちゃった。",
        "Я приготовил строгое лицо. Но ваша поддержка вызвала улыбку."
    ],
    [
        "You help keep the project going. I'll keep Marcos company.",
        "Você ajuda o projeto a continuar. Eu faço companhia para o Marcos.",
        "Tú ayudas a que el proyecto siga. Yo le hago compañía a Marcos.",
        "你帮项目继续前进，我陪着 Marcos。",
        "君はプロジェクトを応援。僕は Marcos のそばにいるね。",
        "Вы помогаете проекту двигаться дальше. Я составлю Маркосу компанию."
    ],
    [
        "Thanks for being here. I've already moved a little closer.",
        "Obrigado por estar aqui. Já cheguei um pouquinho mais perto.",
        "Gracias por estar aquí. Ya me acerqué un poquito más.",
        "谢谢你在这里，我已经悄悄挪近了一点。",
        "ここにいてくれてありがとう。もう少し近くに寄っちゃった。",
        "Спасибо, что вы здесь. Я уже придвинулся чуть поближе."
    ],
    [
        "Your support brought out my happy head tilt.",
        "Seu apoio me fez dar aquela inclinadinha de cabeça de quem ficou feliz.",
        "Tu apoyo me hizo inclinar la cabeza de pura alegría.",
        "你的支持让我开心得歪了歪头。",
        "君の応援で、うれしいときの首かしげが出ちゃった。",
        "От вашей поддержки я радостно склонил голову набок."
    ],
    [
        "A big thank-you from a very small supervisor.",
        "Um obrigado enorme de um fiscal bem pequeno.",
        "Un agradecimiento enorme de un supervisor muy pequeño.",
        "小小监督员送上大大的感谢。",
        "とても小さな監督から、とても大きなありがとう。",
        "Огромное спасибо от совсем маленького надзирателя."
    ],
    [
        "You gave us a reason to celebrate. I supplied the happy dance.",
        "Você deu um motivo para comemorar. Eu entrei com a dancinha.",
        "Nos diste un motivo para celebrar. Yo puse el bailecito.",
        "你给了我们庆祝的理由，我负责跳开心舞。",
        "お祝いする理由をくれたね。ダンスは僕に任せて。",
        "Вы дали повод для праздника. Танец радости — с меня."
    ],
    [
        "Your support deserves a proper thank-you. I even sat up straight.",
        "Seu apoio merece um agradecimento caprichado. Até sentei direito.",
        "Tu apoyo merece unas gracias como es debido. Hasta me senté derechito.",
        "你的支持值得好好道谢，我都坐端正了。",
        "応援にはきちんとお礼を。背筋まで伸ばして座ったよ。",
        "Ваша поддержка заслуживает хорошей благодарности. Я даже сел ровно."
    ],
    [
        "I'm glad you're part of this. My tail seems to agree.",
        "Fico feliz de ter você por aqui. Meu rabo parece concordar.",
        "Me alegra que formes parte de esto. Mi cola parece estar de acuerdo.",
        "很开心有你参与，尾巴看来也同意。",
        "仲間になってくれてうれしい。しっぽも賛成してるみたい。",
        "Рад, что вы с нами. Хвост, кажется, согласен."
    ],
    [
        "Your support means a lot. I came over to say that up close.",
        "Seu apoio importa muito. Vim dizer isso bem de pertinho.",
        "Tu apoyo significa mucho. Vine a decírtelo de cerquita.",
        "你的支持很重要，我特地凑近来说。",
        "君の応援は大切だよ。それを近くで伝えに来たんだ。",
        "Ваша поддержка очень важна. Я подошёл сказать это поближе."
    ],
    [
        "Thanks for joining us. I made room beside me on the sofa.",
        "Obrigado por chegar junto. Abri um espacinho no sofá do meu lado.",
        "Gracias por acompañarnos. Te hice un huequito a mi lado en el sofá.",
        "谢谢你加入，沙发上我旁边给你留了点位置。",
        "一緒にいてくれてありがとう。ソファの隣を少し空けたよ。",
        "Спасибо, что вы с нами. Освободил вам местечко рядом на диване."
    ],
    [
        "You support the project. I support leaning against good humans.",
        "Você apoia o projeto. Eu apoio ficar encostado em gente boa.",
        "Tú apoyas el proyecto. Yo apoyo recostarme en buena gente.",
        "你支持项目，我支持靠着好人待着。",
        "君はプロジェクトを支える。僕はいい人に寄りかかるのを支持する。",
        "Вы поддерживаете проект. А я поддерживаю привычку прислоняться к хорошим людям."
    ],
    [
        "I'd shake your hand to thank you. Then I'd probably sit on your foot.",
        "Eu apertaria sua mão para agradecer. Depois provavelmente sentaria no seu pé.",
        "Te daría la mano para agradecerte. Luego me sentaría sobre tu pie.",
        "想握手谢谢你，然后大概会坐到你脚上。",
        "握手でお礼をしたいな。その後はたぶん君の足に座るよ。",
        "Пожал бы вам руку в благодарность. А потом, наверное, сел бы вам на ногу."
    ],
    [
        "Thanks for being part of this. I know the value of good company.",
        "Obrigado por estar junto nessa. Eu sei dar valor a uma boa companhia.",
        "Gracias por ser parte de esto. Yo sé valorar la buena compañía.",
        "谢谢你一起参与，我懂得珍惜好伙伴。",
        "仲間になってくれてありがとう。一緒にいるありがたさは、僕もよく知ってるよ。",
        "Спасибо, что вы с нами. Я знаю цену хорошей компании."
    ],
    [
        "Your support warms my heart. I'd show you, but there's a lot of fur.",
        "Seu apoio aquece meu coração. Eu mostraria, mas tem muito pelo na frente.",
        "Tu apoyo me calienta el corazón. Te lo mostraría, pero hay mucho pelo delante.",
        "你的支持暖到心里了，可惜毛太多，给你看不到。",
        "応援で心があったかいよ。見せたいけど、毛が多くてね。",
        "Ваша поддержка греет сердце. Показал бы, но шерсть мешает."
    ],
    [
        "Thanks for the kindness. I brought company, as usual.",
        "Obrigado pelo carinho. Trouxe companhia, como de costume.",
        "Gracias por el cariño. Traje compañía, como de costumbre.",
        "谢谢你的好意，我照例带来了陪伴。",
        "優しさをありがとう。いつものように、そばにいるよ。",
        "Спасибо за доброту. Как обычно, пришёл составить компанию."
    ],
    [
        "You're helping us move forward. I'll walk right beside you.",
        "Você ajuda a gente a seguir. Eu vou andando bem do seu lado.",
        "Nos ayudas a seguir. Yo caminaré bien pegadito a ti.",
        "你帮我们往前走，我会紧紧跟在旁边。",
        "前に進む力をくれたね。僕はぴったり隣を歩くよ。",
        "Вы помогаете нам идти дальше. Я пойду совсем рядом с вами."
    ],
    [
        "A grateful little dog would like to borrow your lap for a minute.",
        "Um cachorrinho agradecido gostaria de pegar seu colo emprestado por um minuto.",
        "Un perrito agradecido quisiera tu regazo prestado un minuto.",
        "一只感激的小狗想借你的膝盖坐一分钟。",
        "感謝している小さな犬が、少しだけひざを借りたいそうです。",
        "Один благодарный пёсик хотел бы на минутку устроиться у вас на коленях."
    ],
    [
        "Thanks for being part of our pack. I'm already following you around.",
        "Obrigado por fazer parte da turma. Já estou seguindo você pela casa.",
        "Gracias por ser parte de la manada. Ya te sigo por la casa.",
        "谢谢你成为伙伴，我已经开始跟着你满屋走了。",
        "仲間になってくれてありがとう。もう家じゅうついて歩いちゃう。",
        "Спасибо, что вы в нашей стае. Я уже хожу за вами по дому."
    ],
    [
        "You helped the project. My thank-you needed no keyboard shortcut.",
        "Você ajudou o projeto. Meu obrigado veio sem precisar de atalho.",
        "Ayudaste al proyecto. Mis gracias no necesitaron un atajo de teclado.",
        "你帮了项目，我的谢谢不需要快捷键。",
        "プロジェクトへの応援、ありがとう。お礼にはショートカット不要だよ。",
        "Вы помогли проекту. Для моего спасибо не понадобилась горячая клавиша."
    ],
    [
        "Your support is welcome here. Unlike my paws on the keyboard.",
        "Seu apoio é bem-vindo aqui. Minhas patas no teclado, nem tanto.",
        "Tu apoyo es bienvenido aquí. Mis patas en el teclado, no tanto.",
        "你的支持在这里很受欢迎，我踩键盘可就未必了。",
        "君の応援は大歓迎。キーボードに乗る僕の足は、そうでもないけど。",
        "Ваша поддержка здесь кстати. В отличие от моих лап на клавиатуре."
    ],
    [
        "Thanks for helping. I'm keeping the human from opening one more tab.",
        "Obrigado pela força. Estou tentando impedir o humano de abrir mais uma aba.",
        "Gracias por la ayuda. Intento que mi humano no abra otra pestaña.",
        "谢谢帮忙，我正努力不让人类再开一个标签页。",
        "力を貸してくれてありがとう。人間がまたタブを増やすのを止めてるよ。",
        "Спасибо за помощь. Пытаюсь не дать моему человеку открыть ещё одну вкладку."
    ],
    [
        "Your support made me smile. No reboot required.",
        "Seu apoio me fez sorrir. Nem precisei reiniciar.",
        "Tu apoyo me hizo sonreír. Sin reiniciar siquiera.",
        "你的支持让我笑了，连重启都不用。",
        "君の応援で笑顔になったよ。再起動もいらなかった。",
        "Ваша поддержка вызвала улыбку. Даже перезагружаться не пришлось."
    ],
    [
        "You help with development. I help locate the warmest spot under the desk.",
        "Você ajuda no desenvolvimento. Eu encontro o lugar mais quentinho debaixo da mesa.",
        "Tú ayudas con el desarrollo. Yo encuentro el rincón más cálido bajo la mesa.",
        "你帮开发，我负责找桌子下面最暖和的位置。",
        "君は開発を応援。僕は机の下のいちばん暖かい場所を探す。",
        "Вы помогаете разработке. Я нахожу самое тёплое место под столом."
    ],
    [
        "Thanks for the support. I've stopped judging the cable management for a moment.",
        "Obrigado pelo apoio. Até parei de julgar a bagunça dos cabos por um instante.",
        "Gracias por el apoyo. Dejé un momento de juzgar el lío de cables.",
        "谢谢支持，我都暂时不嫌弃那些乱糟糟的线了。",
        "応援ありがとう。ケーブルの散らかり具合を批評するのを少し休んだよ。",
        "Спасибо за поддержку. Даже перестал на минуту осуждать путаницу проводов."
    ],
    [
        "Your support made me forget what I wanted. Oh, a cuddle. But first: thank you.",
        "Seu apoio me fez esquecer o que eu ia pedir. Ah, carinho. Mas primeiro: obrigado.",
        "Tu apoyo me hizo olvidar qué iba a pedir. Ah, mimos. Pero primero: gracias.",
        "你的支持让我忘了要什么，哦，摸摸。不过先说谢谢。",
        "応援がうれしくて何が欲しかったか忘れたよ。あ、なでなで。でも先にありがとう。",
        "От вашей поддержки забыл, что хотел попросить. А, ласки. Но сначала — спасибо."
    ],
    [
        "Thanks for helping my human build. I'll remind him to take a walk.",
        "Obrigado por ajudar meu humano a construir. Vou lembrar ele de dar uma volta.",
        "Gracias por ayudar a mi humano a crear. Le recordaré que salga a pasear.",
        "谢谢你帮我的人类做东西，我会提醒他出去走走。",
        "僕の人間のものづくりを応援してくれてありがとう。散歩の時間は僕が教えるね。",
        "Спасибо за помощь моему человеку. Я напомню ему выйти прогуляться."
    ],
    [
        "Your support matters. My contribution is not pressing Enter with my nose.",
        "Seu apoio faz diferença. Minha contribuição é não apertar Enter com o focinho.",
        "Tu apoyo cuenta. Mi aportación es no pulsar Enter con el hocico.",
        "你的支持很有用，我的贡献是不用鼻子乱按回车。",
        "君の応援は力になるよ。僕の貢献は、鼻で Enter を押さないこと。",
        "Ваша поддержка важна. Мой вклад — не нажимать Enter носом."
    ],
    [
        "Thanks for the support. I left the keyboard alone so this message would be readable.",
        "Obrigado pelo apoio. Deixei o teclado em paz para este obrigado sair legível.",
        "Gracias por el apoyo. Dejé el teclado en paz para que estas gracias fueran legibles.",
        "谢谢支持，我没碰键盘，好让这句谢谢能看清。",
        "応援ありがとう。ちゃんと読めるお礼になるよう、キーボードには触らなかったよ。",
        "Спасибо за поддержку. Не трогал клавиатуру, чтобы это спасибо можно было прочитать."
    ],
    [
        "Thanks for giving the project a hand. This deserves a proper stretch.",
        "Obrigado por dar uma força ao projeto. Isso merece uma boa espreguiçada.",
        "Gracias por echar una mano al proyecto. Esto merece un buen estirón.",
        "谢谢你给项目搭把手，值得好好伸个懒腰庆祝。",
        "プロジェクトを助けてくれてありがとう。お礼にぐーっと伸びをするよ。",
        "Спасибо, что подставили проекту плечо. Это заслуживает хороших потягушек."
    ],
    [
        "Your support is a good reason to get off my favorite cushion.",
        "Seu apoio é um bom motivo para sair da minha almofada favorita.",
        "Tu apoyo es una buena razón para dejar mi cojín favorito.",
        "你的支持是离开我最爱垫子的好理由。",
        "君の応援なら、お気に入りのクッションから降りてもいいな。",
        "Ради вашей поддержки стоит встать с любимой подушки."
    ],
    [
        "I paused my nap to say thanks. No regrets so far.",
        "Pausei minha soneca para agradecer. Até agora, sem arrependimentos.",
        "Pausé mi siesta para darte las gracias. De momento, sin arrepentimientos.",
        "暂停午睡来道谢，目前不后悔。",
        "お礼のために昼寝を中断したよ。今のところ後悔なし。",
        "Прервал сон, чтобы сказать спасибо. Пока не жалею."
    ],
    [
        "Thanks for helping. I saved you the sunny end of the sofa.",
        "Obrigado pela ajuda. Guardei para você a ponta do sofá que pega sol.",
        "Gracias por ayudar. Te guardé el lado del sofá donde da el sol.",
        "谢谢帮忙，沙发上晒太阳的那头留给你。",
        "応援ありがとう。ソファの日が当たる端を空けておいたよ。",
        "Спасибо за помощь. Оставил вам солнечный край дивана."
    ],
    [
        "Your support made the day better. Even before my first nap.",
        "Seu apoio melhorou o dia. E olha que eu nem tinha tirado a primeira soneca.",
        "Tu apoyo mejoró el día. Y aún no había echado mi primera siesta.",
        "你的支持让今天更好了，连第一次午睡都还没开始呢。",
        "君の応援でいい日になったよ。まだ最初の昼寝もしてないのに。",
        "Ваша поддержка улучшила день. А я ведь ещё даже первый раз не поспал."
    ],
    [
        "Thanks for following the project. I found a good spot to say it: right beside your chair.",
        "Obrigado por acompanhar o projeto. Achei um bom lugar para agradecer: do lado da sua cadeira.",
        "Gracias por seguir el proyecto. Encontré un buen lugar para agradecerte: junto a tu silla.",
        "谢谢你关注项目，我找到了个道谢的好位置：你的椅子旁。",
        "プロジェクトを見守ってくれてありがとう。お礼を言ういい場所を見つけたよ。君の椅子の隣。",
        "Спасибо, что следите за проектом. Нашёл хорошее место для благодарности — рядом с вашим стулом."
    ],
    [
        "That support deserves a thank-you before I roll over for a belly rub.",
        "Esse apoio merece um obrigado antes de eu virar de barriga para cima.",
        "Ese apoyo merece unas gracias antes de que me tumbe para pedir mimos.",
        "这份支持值得先说声谢谢，再翻肚皮求摸摸。",
        "応援にありがとう。それから、おなかを見せてなでてもらおうかな。",
        "За такую поддержку сначала спасибо. А потом перевернусь за почесушками."
    ],
    [
        "Thanks for being here. This is the happy face I usually save for walks.",
        "Obrigado por estar aqui. Essa é a cara feliz que eu costumo guardar para os passeios.",
        "Gracias por estar aquí. Esta cara feliz suelo reservarla para los paseos.",
        "谢谢你来，这张开心脸平常散步时才拿出来。",
        "ここにいてくれてありがとう。これは普段、お散歩のときのうれしい顔だよ。",
        "Спасибо, что вы здесь. Такое счастливое лицо я обычно берегу для прогулок."
    ],
    [
        "I was lying down, thinking about nothing. Your support gave me a good reason to get up and say thanks.",
        "Eu estava deitado pensando em nada. Seu apoio me deu um bom motivo para levantar e agradecer.",
        "Estaba tumbado sin pensar en nada. Tu apoyo me dio un buen motivo para levantarme y agradecerte.",
        "本来正躺着发呆，你的支持给了我起来道谢的好理由。",
        "寝そべって何も考えてなかったけど、応援のおかげで起きてお礼を言いたくなったよ。",
        "Лежал и ни о чём не думал. Ваша поддержка дала хороший повод встать и поблагодарить."
    ],
    [
        "Thanks for the support. I'm wagging from the comfort of my blanket.",
        "Obrigado pelo apoio. Estou abanando daqui de dentro da coberta.",
        "Gracias por el apoyo. Estoy moviendo la cola desde dentro de mi manta.",
        "谢谢支持，我正舒服地窝在毯子里摇尾巴。",
        "応援ありがとう。毛布の中からしっぽを振ってるよ。",
        "Спасибо за поддержку. Виляю хвостом, не вылезая из-под пледа."
    ],
    [
        "Your support helps a little project take bigger steps. Mine are still short.",
        "Seu apoio ajuda um projeto pequeno a dar passos maiores. Os meus continuam curtinhos.",
        "Tu apoyo ayuda a un proyecto pequeño a dar pasos más grandes. Los míos siguen siendo cortitos.",
        "你的支持让小项目迈大步，我的步子还是短短的。",
        "小さなプロジェクトが大きな一歩を踏み出せるね。僕の歩幅は短いままだけど。",
        "С вашей поддержкой маленький проект шагает шире. Мои шаги всё ещё короткие."
    ],
    [
        "Your support made me feel taller. I might just be sitting on a cushion.",
        "Seu apoio me deixou até mais alto. Talvez eu só tenha sentado em cima da almofada.",
        "Tu apoyo me hizo sentir más alto. Quizá solo me senté sobre un cojín.",
        "你的支持让我都长高了，也许只是坐在垫子上了。",
        "応援で背が高くなった気分。クッションに座っただけかもしれないけど。",
        "От вашей поддержки я будто стал выше. Возможно, просто сел на подушку."
    ],
    [
        "I'd give you a thank-you high five. Please excuse the fur.",
        "Eu te daria um toca aqui de agradecimento. Não repare nos pelos.",
        "Te daría esos cinco para agradecerte. Disculpa los pelos.",
        "想击掌谢谢你，请别介意爪子上的毛。",
        "ありがとうのハイタッチをどうぞ。毛は気にしないでね。",
        "Дал бы вам пять в благодарность. За шерсть заранее извините."
    ],
    [
        "Your support is a big deal to this little dog.",
        "Seu apoio é coisa grande para este cachorro pequeno.",
        "Tu apoyo es algo grande para este perro pequeño.",
        "你的支持，对小小的我来说是大事。",
        "君の応援は、この小さな犬にとって大きなことなんだ。",
        "Ваша поддержка — большое дело для этого маленького пса."
    ],
    [
        "I tried to count all my thanks. Four paws weren't enough.",
        "Tentei contar todos os meus obrigados. Quatro patas não deram conta.",
        "Intenté contar todos mis agradecimientos. Cuatro patas no bastaron.",
        "想把所有谢谢数一遍，四只爪子都不够。",
        "ありがとうを全部数えようとしたけど、四本の足じゃ足りなかった。",
        "Пытался пересчитать все свои спасибо. Четырёх лап не хватило."
    ],
    [
        "Thanks for helping. My little victory trot is entirely for you.",
        "Obrigado pela força. Esse trotinho de comemoração é todo seu.",
        "Gracias por la ayuda. Este trotecito de celebración es para ti.",
        "谢谢帮忙，这段庆祝小跑专门送给你。",
        "応援ありがとう。このお祝いの小走りは君のためだよ。",
        "Спасибо за помощь. Эта радостная пробежка — для вас."
    ],
    [
        "Your support helps the project move forward. I'm coming too, sniffing everything on the way.",
        "Seu apoio ajuda o projeto a seguir. Eu vou junto, parando para cheirar tudo.",
        "Tu apoyo ayuda al proyecto a avanzar. Yo voy también, parando a olerlo todo.",
        "你的支持帮项目前进，我也跟着，一路什么都闻闻。",
        "君の応援で前に進めるね。僕も途中で何でもくんくんしながらついていくよ。",
        "Ваша поддержка помогает проекту идти дальше. Я тоже иду, обнюхивая всё по пути."
    ],
    [
        "Your kindness got a little hop of gratitude. Very little. Short legs.",
        "Sua gentileza ganhou um pulinho de gratidão. Bem pequeno. Perninhas curtas.",
        "Tu amabilidad se ganó un saltito de gratitud. Pequeñito. Patitas cortas.",
        "你的好意换来了感激的一小跳，真的很小，腿短嘛。",
        "感謝のぴょんをひとつ。ほんの少しね、足が短いから。",
        "За вашу доброту — благодарный прыжочек. Маленький. Лапки короткие."
    ],
    [
        "Thank you. If gratitude left paw prints, this page would be covered.",
        "Obrigado. Se gratidão deixasse pegadas, essa página estaria cheia delas.",
        "Gracias. Si la gratitud dejara huellas, esta página estaría llena.",
        "谢谢，要是感谢会留下爪印，这页早就铺满了。",
        "ありがとう。感謝が足あとになるなら、このページはいっぱいだね。",
        "Спасибо. Если бы благодарность оставляла следы лап, здесь было бы полно следов."
    ],
    [
        "You helped us take another step. I celebrated by walking in a tiny circle.",
        "Você ajudou a dar mais um passo. Comemorei dando uma voltinha em círculo.",
        "Nos ayudaste a dar otro paso. Lo celebré dando una vueltecita.",
        "你帮我们又走了一步，我开心地转了个小圈。",
        "次の一歩を助けてくれたね。うれしくて小さく一周しちゃった。",
        "Вы помогли сделать ещё шаг. От радости я прошёл маленький кружок."
    ],
    [
        "Your support made this galaxy feel a bit more like home.",
        "Seu apoio deixou essa galáxia um pouco mais com cara de casa.",
        "Tu apoyo hizo que esta galaxia se sintiera un poco más como casa.",
        "你的支持让这片星系更像家了。",
        "君の応援で、この銀河が少し家みたいに感じるよ。",
        "С вашей поддержкой эта галактика стала чуть больше похожа на дом."
    ],
    [
        "Thanks for joining our little corner of the universe. I saved you some space.",
        "Obrigado por chegar ao nosso cantinho do universo. Guardei um espaço para você.",
        "Gracias por llegar a nuestro rincón del universo. Te guardé un espacio.",
        "谢谢你来到宇宙里的这个小角落，给你留了位置。",
        "宇宙の小さな片隅へようこそ。君の場所を空けておいたよ。",
        "Спасибо, что вы с нами в этом уголке вселенной. Место для вас я оставил."
    ],
    [
        "Your kindness is a bright spot here. I'm doing my best not to chase it.",
        "Sua gentileza é um ponto de luz por aqui. Estou me segurando para não correr atrás.",
        "Tu amabilidad es un punto de luz aquí. Me aguanto las ganas de perseguirlo.",
        "你的善意是这里的亮点，我努力忍着不去追。",
        "君の優しさが光ってる。追いかけないよう頑張ってるよ。",
        "Ваша доброта здесь как огонёк. Стараюсь не бежать за ним."
    ],
    [
        "Thanks for the support. I'm trying not to bark at the comets while I say it.",
        "Obrigado pelo apoio. Estou tentando não latir para os cometas enquanto agradeço.",
        "Gracias por el apoyo. Intento no ladrar a los cometas mientras te lo digo.",
        "谢谢支持，我道谢时正努力不对着彗星汪汪。",
        "応援ありがとう。お礼を言う間、彗星に吠えないようにしてるよ。",
        "Спасибо за поддержку. Стараюсь не лаять на кометы, пока благодарю."
    ],
    [
        "Thanks for the support. Even a space dog needs good company.",
        "Obrigado pelo apoio. Até cachorro espacial precisa de boa companhia.",
        "Gracias por el apoyo. Hasta un perro espacial necesita buena compañía.",
        "谢谢支持，太空狗狗也需要好伙伴。",
        "応援ありがとう。宇宙の犬にも、いい仲間が必要なんだ。",
        "Спасибо за поддержку. Даже космическому псу нужна хорошая компания."
    ],
    [
        "Thanks for the support. My sense of direction isn't great, but I came straight over to thank you.",
        "Obrigado pela força. Meu senso de direção é duvidoso, mas vim direto agradecer.",
        "Gracias por la ayuda. Me oriento regular, pero vine directo a agradecerte.",
        "谢谢帮助，我方向感不怎么样，可道谢是直接来的。",
        "応援ありがとう。方向音痴だけど、お礼にはまっすぐ来たよ。",
        "Спасибо за помощь. С направлением у меня не очень, но благодарить пришёл прямо к вам."
    ],
    [
        "You help this project find its way. I still get distracted by the flying bones.",
        "Você ajuda o projeto a seguir seu caminho. Eu ainda me distraio com os ossinhos voando.",
        "Ayudas al proyecto a seguir su camino. Yo aún me distraigo con los huesitos voladores.",
        "你帮项目找到方向，我还是会被飞骨头分心。",
        "プロジェクトの道を支えてくれてありがとう。僕はまだ飛ぶ骨によそ見しちゃう。",
        "Вы помогаете проекту идти своим путём. Я всё ещё отвлекаюсь на летающие косточки."
    ],
    [
        "Thanks for being here. That's a happy little dog in a very big universe.",
        "Obrigado por estar aqui. É um cachorrinho bem feliz num universo bem grande.",
        "Gracias por estar aquí. Hay un perrito muy feliz en un universo muy grande.",
        "谢谢你在这里，宇宙很大，小狗很开心。",
        "ここにいてくれてありがとう。大きな宇宙で、小さな犬が喜んでるよ。",
        "Спасибо, что вы здесь. Маленький пёсик очень счастлив в этой большой вселенной."
    ],
    [
        "Thanks for the company in this galaxy. I still prefer walks with all four paws on the ground.",
        "Obrigado pela companhia nesta galáxia. Ainda prefiro passear com as quatro patas no chão.",
        "Gracias por la compañía en esta galaxia. Aún prefiero pasear con las cuatro patas en el suelo.",
        "谢谢在星系里陪伴，我还是喜欢四爪着地散步。",
        "銀河で一緒にいてくれてありがとう。でも散歩は四本の足を地面につけるほうが好きだな。",
        "Спасибо за компанию в этой галактике. Но гулять я всё-таки предпочитаю всеми четырьмя лапами по земле."
    ],
    [
        "Thanks for bringing some life to this galaxy. I was about to doze off in orbit.",
        "Obrigado por deixar esta galáxia mais animada. Eu já estava quase cochilando em órbita.",
        "Gracias por darle vida a esta galaxia. Ya casi me dormía en órbita.",
        "谢谢你让星系热闹起来，我差点就在轨道上打瞌睡了。",
        "この銀河をにぎやかにしてくれてありがとう。軌道の上でうとうとするところだったよ。",
        "Спасибо, что оживили эту галактику. Я уже чуть не задремал на орбите."
    ],
    [
        "Thank you for the support. I'm smiling like I heard the treat jar.",
        "Obrigado pelo apoio. Estou sorrindo como quem ouviu o pote de petiscos.",
        "Gracias por el apoyo. Sonrío como si hubiera oído el bote de premios.",
        "谢谢支持，我笑得像刚听见零食罐响。",
        "応援ありがとう。おやつの瓶の音を聞いたみたいに笑ってるよ。",
        "Спасибо за поддержку. Улыбаюсь, будто услышал банку с вкусняшками."
    ],
    [
        "Your kindness deserves a thank-you before I ask about snacks.",
        "Sua gentileza merece um obrigado antes de eu perguntar pelos petiscos.",
        "Tu amabilidad merece unas gracias antes de que pregunte por los premios.",
        "先谢谢你的好意，再问零食在哪儿。",
        "優しさにまずありがとう。その後でおやつの話をしようかな。",
        "За вашу доброту сначала спасибо. А уж потом спрошу про вкусняшки."
    ],
    [
        "Thanks for helping the project. You got my happy face without opening the fridge.",
        "Obrigado por ajudar o projeto. Você ganhou minha cara feliz sem abrir a geladeira.",
        "Gracias por ayudar al proyecto. Te llevaste mi cara feliz sin abrir la nevera.",
        "谢谢你帮项目，不用开冰箱就得到了我的开心脸。",
        "プロジェクトへの応援ありがとう。冷蔵庫を開けずに、僕を笑顔にしたね。",
        "Спасибо за помощь проекту. Моё счастливое лицо вы получили, даже не открывая холодильник."
    ],
    [
        "Your support made me do the little dance usually reserved for dinner.",
        "Seu apoio me fez dar a dancinha que eu costumo guardar para a janta.",
        "Tu apoyo me hizo bailar como suelo hacerlo a la hora de cenar.",
        "你的支持让我跳起了平时等晚饭才跳的小舞。",
        "君の応援で、普段ごはんのときに踊るダンスが出ちゃった。",
        "От вашей поддержки я станцевал так, как обычно танцую перед ужином."
    ],
    [
        "Thanks for the care. It means more than a very nice biscuit.",
        "Obrigado pelo carinho. Vale mais que um biscoito dos bons.",
        "Gracias por el cariño. Vale más que una galleta de las buenas.",
        "谢谢你的关心，比一块超好吃的饼干还珍贵。",
        "優しさをありがとう。とびきりのビスケットより大切だよ。",
        "Спасибо за заботу. Она дороже даже очень хорошего печенья."
    ],
    [
        "Thanks for helping the project. This thank-you is free of biscuit crumbs.",
        "Você ajudou o projeto. Este obrigado vem sem farelo de biscoito.",
        "Gracias por ayudar al proyecto. Estas gracias vienen sin migas de galleta.",
        "谢谢你帮项目，这份感谢不沾饼干屑。",
        "プロジェクトを助けてくれてありがとう。このお礼にはビスケットのくずは付いてないよ。",
        "Спасибо за помощь проекту. Это спасибо без крошек печенья."
    ],
    [
        "Your support has my attention. And I wasn't even bribed with cheese.",
        "Seu apoio tem minha atenção. E nem precisou me subornar com queijo.",
        "Tu apoyo tiene mi atención. Y ni siquiera hubo soborno con queso.",
        "你的支持让我认真听着，都没用奶酪收买我。",
        "君の応援に注目してるよ。チーズでつられたわけでもないのに。",
        "Ваша поддержка привлекла моё внимание. И даже сыром подкупать не пришлось."
    ],
    [
        "Thanks for lending the project a hand. Here's a paw, no treat required.",
        "Obrigado por dar uma mão ao projeto. A pata vai junto, sem pedir petisco.",
        "Gracias por echar una mano al proyecto. Te doy la pata sin pedir premio.",
        "谢谢你给项目搭把手，我也递只爪子，不讨零食。",
        "プロジェクトに手を貸してくれてありがとう。おやつなしでもお手するよ。",
        "Спасибо, что протянули проекту руку. Лапу даю и без угощения."
    ],
    [
        "Your kindness put a smile on this face. That's usually the kitchen's job.",
        "Sua gentileza abriu esse sorriso. Geralmente esse serviço é da cozinha.",
        "Tu amabilidad me sacó esta sonrisa. Normalmente eso lo consigue la cocina.",
        "你的好意让我笑开了，平时这事归厨房管。",
        "君の優しさでこの笑顔。いつもはキッチンの担当なんだけどね。",
        "Ваша доброта вызвала эту улыбку. Обычно это работа кухни."
    ],
    [
        "Thanks for supporting us. This excitement is homemade, no treats added.",
        "Obrigado por apoiar a gente. Essa alegria é caseira, sem adição de petiscos.",
        "Gracias por apoyarnos. Esta alegría es casera, sin premios añadidos.",
        "谢谢支持我们，这份开心是自制的，没加零食。",
        "応援ありがとう。この喜びは手作り、おやつ無添加だよ。",
        "Спасибо за поддержку. Эта радость домашняя, без добавления вкусняшек."
    ],
    [
        "Your support got past my serious glasses and straight to the smile.",
        "Seu apoio passou pelos óculos sérios e foi direto para o sorriso.",
        "Tu apoyo atravesó mis gafas serias y llegó directo a la sonrisa.",
        "你的支持穿过严肃的眼镜，直达笑容。",
        "君の応援がまじめな眼鏡を通り抜けて、笑顔に届いたよ。",
        "Ваша поддержка прошла сквозь серьёзные очки прямо к улыбке."
    ],
    [
        "I adjusted my glasses to say thanks. Entirely unnecessary, very professional.",
        "Ajeitei os óculos para agradecer. Desnecessário, mas muito profissional.",
        "Me ajusté las gafas para agradecerte. Innecesario, pero muy profesional.",
        "扶了扶眼镜来道谢，完全没必要，但很专业。",
        "お礼のために眼鏡を直したよ。不要だけど、とてもプロらしいでしょ。",
        "Поправил очки, чтобы поблагодарить. Совсем не нужно, зато очень профессионально."
    ],
    [
        "Thanks for helping. You caught me looking pleased instead of important.",
        "Obrigado pela ajuda. Você me pegou com cara de feliz em vez de importante.",
        "Gracias por ayudar. Me pillaste con cara de feliz en vez de importante.",
        "谢谢帮忙，被你撞见我在开心，而不是摆架子。",
        "応援ありがとう。えらそうな顔じゃなく、うれしい顔を見られちゃったね。",
        "Спасибо за помощь. Вы застали меня довольным, а не важным."
    ],
    [
        "Your kindness made me lower an eyebrow. That's my version of applause.",
        "Sua gentileza me fez baixar uma sobrancelha. É meu jeito de aplaudir.",
        "Tu amabilidad me hizo bajar una ceja. Es mi forma de aplaudir.",
        "你的好意让我放下了一边眉毛，这是我的鼓掌方式。",
        "君の優しさで眉が片方下がったよ。これが僕なりの拍手。",
        "От вашей доброты я опустил одну бровь. Так я аплодирую."
    ],
    [
        "Thanks for supporting a project with my name. Can I sign this thank-you with a paw print?",
        "Obrigado por apoiar um projeto com meu nome. Posso assinar este obrigado com uma patinha?",
        "Gracias por apoyar un proyecto con mi nombre. ¿Puedo firmar estas gracias con una huella?",
        "谢谢你支持用我名字命名的项目，能用爪印在这份感谢上签名吗？",
        "僕の名前のプロジェクトを応援してくれてありがとう。このお礼、肉球でサインしていい？",
        "Спасибо за поддержку проекта с моим именем. Можно подписать это спасибо отпечатком лапы?"
    ],
    [
        "You helped the project and ruined my attempt to look mysterious.",
        "Você ajudou o projeto e estragou minha tentativa de fazer mistério. Acabei sorrindo.",
        "Ayudaste al proyecto y arruinaste mi intento de parecer misterioso. Acabé sonriendo.",
        "你帮了项目，还打破了我的神秘感，害我笑出来了。",
        "プロジェクトを応援してくれて、謎めいた顔のつもりが笑顔になっちゃった。",
        "Вы помогли проекту и сорвали мою попытку выглядеть загадочно. Я улыбнулся."
    ],
    [
        "A sincere thank-you from behind these very serious lenses.",
        "Um obrigado sincero por trás dessas lentes muito sérias.",
        "Unas gracias sinceras desde detrás de estas lentes tan serias.",
        "从这副严肃镜片后面，送上一句真心谢谢。",
        "このまじめなレンズの奥から、心をこめてありがとう。",
        "Искреннее спасибо из-за этих очень серьёзных стёкол."
    ],
    [
        "Your support made the little supervisor proud. The chest puff is accidental.",
        "Seu apoio deixou o fiscalzinho orgulhoso. O peito estufado foi sem querer.",
        "Tu apoyo llenó de orgullo al supervisor. Lo de sacar pecho fue sin querer.",
        "你的支持让小监督员很骄傲，挺起胸是无意的。",
        "応援で小さな監督は誇らしいよ。胸を張ったのは、ついね。",
        "От вашей поддержки маленький надзиратель гордится. Грудь выпятил случайно."
    ],
    [
        "Thanks for believing in us. I'm trying not to look too pleased with myself.",
        "Obrigado por acreditar na gente. Estou tentando disfarçar a cara de convencido.",
        "Gracias por creer en nosotros. Intento disimular mi cara de presumido.",
        "谢谢你相信我们，我努力藏住得意的表情。",
        "信じてくれてありがとう。得意げな顔を隠そうとしてるよ。",
        "Спасибо, что верите в нас. Пытаюсь скрыть самодовольную мордочку."
    ],
    [
        "Your kindness got a proper thank-you. The raised eyebrow is just how I look.",
        "Sua gentileza ganhou um obrigado de verdade. A sobrancelha é assim mesmo.",
        "Tu amabilidad recibió unas gracias de verdad. La ceja es así de fábrica.",
        "真心谢谢你的好意，眉毛天生就这样。",
        "優しさにはちゃんとお礼を言うよ。眉が上がっているのは生まれつき。",
        "За вашу доброту — настоящее спасибо. Бровь у меня просто такая."
    ],
    [
        "Thanks for helping Marcos build. I make sure he knows when it's walk time.",
        "Obrigado por ajudar o Marcos a construir. Eu aviso quando é hora do passeio.",
        "Gracias por ayudar a Marcos a crear. Yo aviso cuando toca paseo.",
        "谢谢你帮 Marcos 做项目，我会提醒他散步时间到了。",
        "Marcos の開発を応援してくれてありがとう。散歩の時間は僕がお知らせするね。",
        "Спасибо за помощь Маркосу. Я сообщаю ему, когда пора гулять."
    ],
    [
        "Your support helps the work continue. My job is to be underfoot.",
        "Seu apoio ajuda o trabalho a continuar. Meu trabalho é ficar no caminho.",
        "Tu apoyo ayuda a que el trabajo siga. Mi trabajo es estar en medio.",
        "你的支持让工作继续，我的工作是在脚边挡路。",
        "君の応援で作業が続けられるね。僕の仕事は足元にいること。",
        "С вашей поддержкой работа продолжается. Моя работа — путаться под ногами."
    ],
    [
        "You give the project a boost. I give Marcos a reason to leave the chair.",
        "Você dá uma força ao projeto. Eu dou um motivo para o Marcos sair da cadeira.",
        "Tú impulsas el proyecto. Yo le doy a Marcos un motivo para levantarse.",
        "你给项目助力，我给 Marcos 一个离开椅子的理由。",
        "君はプロジェクトに力を。僕は Marcos に椅子から立つ理由を。",
        "Вы помогаете проекту. Я даю Маркосу повод встать со стула."
    ],
    [
        "Thanks for supporting the project. I'm celebrating carefully; Marcos has a coffee on the desk.",
        "Obrigado por apoiar o projeto. Estou comemorando com cuidado: tem café na mesa do Marcos.",
        "Gracias por apoyar el proyecto. Celebro con cuidado: Marcos tiene café en la mesa.",
        "谢谢你支持项目，我小心地庆祝，Marcos 桌上还放着咖啡。",
        "プロジェクトを応援してくれてありがとう。お祝いは慎重にね。Marcos の机にコーヒーがあるから。",
        "Спасибо за поддержку проекта. Праздную осторожно: у Маркоса на столе кофе."
    ],
    [
        "Your support helps the project grow. I'm planning to stay this size.",
        "Seu apoio ajuda o projeto a crescer. Eu pretendo continuar deste tamanho.",
        "Tu apoyo ayuda al proyecto a crecer. Yo pienso quedarme de este tamaño.",
        "你的支持帮项目成长，我打算保持这个体型。",
        "応援でプロジェクトは大きくなるね。僕はこの大きさのままでいるつもり。",
        "С вашей поддержкой проект растёт. Я собираюсь остаться такого размера."
    ],
    [
        "Thanks for being part of the work. I attend meetings from the floor.",
        "Obrigado por fazer parte desse trabalho. Participo das reuniões lá do chão.",
        "Gracias por formar parte del trabajo. Yo asisto a las reuniones desde el suelo.",
        "谢谢你参与这份工作，我在地板上参加会议。",
        "この仕事に加わってくれてありがとう。僕は床から会議に参加するよ。",
        "Спасибо, что участвуете в работе. Я хожу на совещания прямо с пола."
    ],
    [
        "You help us keep building. I handle the breaks where someone scratches my ears.",
        "Você ajuda a gente a continuar criando. Eu cuido das pausas para carinho nas orelhas.",
        "Nos ayudas a seguir creando. Yo me encargo de las pausas para rascarme las orejas.",
        "你帮我们继续开发，我负责安排摸耳朵的休息时间。",
        "作り続ける力をくれてありがとう。耳をなでてもらう休憩は僕の担当。",
        "Вы помогаете нам продолжать. Я отвечаю за перерывы на почесать за ушами."
    ],
    [
        "Thanks for giving this idea a chance. I gave it my name and most of the fur.",
        "Obrigado por dar uma chance à ideia. Eu entrei com o nome e boa parte dos pelos.",
        "Gracias por darle una oportunidad a la idea. Yo puse el nombre y buena parte del pelo.",
        "谢谢你给这个想法机会，我贡献了名字和不少毛。",
        "このアイデアにチャンスをくれてありがとう。僕は名前とたくさんの毛を提供したよ。",
        "Спасибо, что дали идее шанс. Я вложил имя и большую часть шерсти."
    ],
    [
        "Your support makes a difference. My supervision is mostly moral support from a cushion.",
        "Seu apoio faz diferença. Minha supervisão é mais um apoio moral da almofada.",
        "Tu apoyo marca la diferencia. Mi supervisión es más bien apoyo moral desde un cojín.",
        "你的支持很有用，我的监督主要是躺在垫子上精神支持。",
        "君の応援は力になるよ。僕の監督は、主にクッションからの応援だけどね。",
        "Ваша поддержка важна. Мой надзор — в основном моральная поддержка с подушки."
    ],
    [
        "Thanks for supporting this small project. The dog on the logo is very touched.",
        "Obrigado por apoiar esse pequeno projeto. O cachorro do logo ficou todo bobo.",
        "Gracias por apoyar este pequeño proyecto. El perro del logo se emocionó mucho.",
        "谢谢你支持这个小项目，标志上的狗狗感动坏了。",
        "この小さなプロジェクトを応援してくれてありがとう。ロゴの犬もじんとしてるよ。",
        "Спасибо за поддержку маленького проекта. Пёс на логотипе очень тронут."
    ],
    [
        "Your kindness means a lot. I brought a thank-you and a little too much enthusiasm.",
        "Sua gentileza importa muito. Trouxe um obrigado e um pouquinho de empolgação a mais.",
        "Tu amabilidad significa mucho. Traje unas gracias y un poquito de entusiasmo de más.",
        "你的好意很重要，我带来了谢谢，还有一点过量的热情。",
        "君の優しさは大切だよ。ありがとうと、少し多めのはしゃぎっぷりを持ってきた。",
        "Ваша доброта очень важна. Принёс спасибо и немного лишнего восторга."
    ],
    [
        "Thanks for joining the project. I'm trying not to trip over my own excitement.",
        "Obrigado por se juntar ao projeto. Estou tentando não tropeçar na própria empolgação.",
        "Gracias por sumarte al proyecto. Intento no tropezar con mi propia emoción.",
        "谢谢你加入项目，我正努力不开心得绊倒自己。",
        "プロジェクトに加わってくれてありがとう。はしゃいで転ばないようにしてるよ。",
        "Спасибо, что присоединились к проекту. Стараюсь не споткнуться от радости."
    ],
    [
        "Your support deserves a quiet, sincere thank-you. My tail didn't get the quiet part.",
        "Seu apoio merece um obrigado calmo e sincero. Meu rabo não entendeu a parte do calmo.",
        "Tu apoyo merece unas gracias tranquilas y sinceras. Mi cola no entendió lo de tranquilas.",
        "想平静真诚地感谢你的支持，可尾巴没听懂平静那部分。",
        "落ち着いて心からありがとう。しっぽは落ち着くほうを理解してないみたい。",
        "За вашу поддержку — спокойное искреннее спасибо. Хвост не понял часть про спокойствие."
    ],
    [
        "Thanks for making room for this project. I'll try to take up less of the sofa.",
        "Obrigado por abrir espaço para o projeto. Vou tentar ocupar menos espaço no sofá.",
        "Gracias por hacer sitio al proyecto. Intentaré ocupar menos sofá.",
        "谢谢你给项目留出空间，我尽量少占一点沙发。",
        "プロジェクトに場所をくれてありがとう。僕もソファを少し空けるようにするね。",
        "Спасибо, что нашли место проекту. Постараюсь занимать поменьше дивана."
    ],
    [
        "You didn't have to help. That makes this thank-you a little bigger than me.",
        "Você não precisava ajudar. Por isso, este obrigado ficou um pouco maior que eu.",
        "No tenías que ayudar. Por eso estas gracias son un poquito más grandes que yo.",
        "你本来不必帮忙，所以这份谢谢比我还大一点。",
        "応援は義務じゃない。だから、このありがとうは僕より少し大きいんだ。",
        "Вы не обязаны были помогать. Поэтому это спасибо чуть больше меня самого."
    ],
    [
        "Your support means we're not doing this alone. I like having company.",
        "Seu apoio mostra que a gente não está sozinho. Eu gosto muito de companhia.",
        "Tu apoyo nos recuerda que no estamos solos. A mí me encanta la compañía.",
        "你的支持说明我们并不孤单，我特别喜欢有伴。",
        "君の応援で、一人きりじゃないと分かるよ。僕は一緒にいるのが好きなんだ。",
        "Ваша поддержка показывает, что мы не одни. А я очень люблю компанию."
    ],
    [
        "Thank you for the encouragement. This head tilt is saying more than I can type.",
        "Obrigado pelo incentivo. Essa inclinadinha de cabeça diz mais do que eu consigo digitar.",
        "Gracias por los ánimos. Esta inclinación de cabeza dice más de lo que puedo escribir.",
        "谢谢鼓励，这个歪头比我打字能说的还多。",
        "励ましてくれてありがとう。この首かしげは、僕が打てる言葉より多くを伝えてるよ。",
        "Спасибо за ободрение. Этот наклон головы говорит больше, чем я могу напечатать."
    ],
    [
        "Your kindness reached a human and his very pleased little dog.",
        "Sua gentileza chegou a um humano e ao cachorrinho todo contente dele.",
        "Tu amabilidad llegó a un humano y a su perrito encantado.",
        "你的好意传达给了一个人类和他开心的小狗。",
        "君の優しさは、一人の人間とごきげんな小さな犬に届いたよ。",
        "Ваша доброта дошла до человека и его очень довольного пёсика."
    ],
    [
        "Thanks for helping us keep going. I brought the grateful look, not the dramatic sigh.",
        "Obrigado por ajudar a gente a continuar. Hoje trouxe o olhar agradecido, não o suspiro dramático.",
        "Gracias por ayudarnos a seguir. Hoy traje la mirada agradecida, no el suspiro dramático.",
        "谢谢你帮我们继续，今天送上感激眼神，不是夸张叹气。",
        "続ける力をくれてありがとう。今日は大げさなため息じゃなく、感謝のまなざしだよ。",
        "Спасибо, что помогаете продолжать. Сегодня — благодарный взгляд, без драматичного вздоха."
    ],
    [
        "A proper thank-you, one more little wag, and a very happy supervisor.",
        "Um obrigado de verdade, mais uma abanadinha e um fiscal muito feliz.",
        "Unas gracias de verdad, otro meneo de cola y un supervisor muy feliz.",
        "一句真心谢谢，再摇一下尾巴，小监督员非常开心。",
        "心からのありがとうと、もうひとふりのしっぽ。監督は大喜びだよ。",
        "Настоящее спасибо, ещё одно виляние хвостом — и очень счастливый надзиратель."
    ]
];
    window.TODDY_SUPPORTER_THANKS = lines.map(([english]) => english);
    for (const [english, ...translations] of lines) window.TODDY_TRANSLATIONS[english] = translations;
})();
