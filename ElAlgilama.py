import numpy as np
import math
import cv2
import pyautogui



# merkez noktayi bulan ve bir tuple değer döndüren fonksiyon
def merkezNoktayiBul(contour):
    M = cv2.moments(contour)
    mX = int(M["m10"] / M["m00"])
    mY = int(M["m01"] / M["m00"])
    return (mX, mY)


cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
eskiKacParmakAcmis = -1
merkezBirParmakx = 1
merkezIkiParmaky = 1
eskiMerkezBirParmakx = 0
eskiMerkezIkiParmaky = 0
kackere3yapmis=0
eskiKacParmakAcmis = 4
# sonsuz dongu.Ekran kapatıldığında bu döngü kırılacak bu döngü kırılacak
while True:
    try:
        # cap değişkeninden bir frame okundu
        ret, frame = cap.read()
        # eğer okunamadıysa ret degeri 0 dondurur,bu sayede sonsuz dongu kırılır.
        if ret == 0:
            break
        # y eksenine göre simetrisi alındı, bu kişinin webcamden
        # videosu alınırken bilgisayar ekranına baktığında
        # aynaya bakıyormuş gibi görmesini sağlayacak
        frame = cv2.flip(frame, 1)
        # rest of ıntrest alanı belirlendi,sadece bu alan içinde konumlandırılan eller göz önüne alınacak
        roi = frame[100:350, 50:300]
        # roi alanı bir dikdortgen ile kulanıcıya bildirildi
        cv2.rectangle(frame, (50, 100), (300, 350), (0, 255, 0), 0)
        # roi bgr renk formatında hsv renk formatına çevrildi ve bu dönüşüm hsv_roi ye gönderildi
        hsv_roi = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
        # deneme yanılma yoluyla elde edilen deneysel değerler lower
        # ve upper color değişkenlerine numpy classının array
        # oluşturma fonksiyonu ile gönderildi,datatype uint8
        lower_hsv = np.array([8, 81, 0], np.uint8)
        upper_hsv = np.array([20, 255, 255], np.uint8)
        # lower ve upper colorlar roiye uygulanıp mask_roiye gönderildi
        mask_roi = cv2.inRange(hsv_roi, lower_hsv, upper_hsv)
        # bir resim manipule etmek için bir kernel oluşturuldu
        kernel = np.ones((3, 3), np.uint8)
        # 1 lerden oluşan kernel sayesinde 1 kere doldurma manipulasyonu uygulandı
        mask_roi = cv2.dilate(mask_roi, kernel, iterations=2)
        # resimdeki kum tanecikleri yumuşatıldı
        mask_roi = cv2.GaussianBlur(mask_roi, (5, 5), 100)

        # mask_roinin contourları bulundu
        contours, _ = cv2.findContours(mask_roi, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        # en büyük alana sahip olan contour u contour değişkenine attık
        contour = max(contours, key=lambda x: cv2.contourArea(x))
        # deneysel bir değer olan epsilon oluşturuldu.(arcLength sınıfın çevresini dondurur , içinde bulunan true
        # değeri) contorun kapalı olduğunu gösterir
        epsilon = 0.0005 * cv2.arcLength(contour, True)
        approx = cv2.approxPolyDP(contour, epsilon, True)
        # cv2.putText fonksiyonunda kullanılmak üzere bir yazı fontu belirlendi
        font = cv2.FONT_HERSHEY_SIMPLEX
        # elin en dış noktalarını baz alarak noktalardan geçecek şekilde bir örtü çizen fonksiyonu kullanıldı
        hull = cv2.convexHull(contour)
        # el algılandığında ayırt edici özellikleri olan elin alanı, çizilen
        # örtünün alanı ve bu iki alanın birbirine oranı hesaplandı
        area_hull = cv2.contourArea(hull)
        area_hand = cv2.contourArea(contour)
        area_ratio = ((area_hull - area_hand) / area_hand) * 100
        # örtüyü tutan hul fonksiyonu approx ile daha fazla yaklaştırılmış bir şekilde çizildi
        hull = cv2.convexHull(approx, returnPoints=False)
        # kusurlar tespit edildi
        defects = cv2.convexityDefects(approx, hull)

        ayirtEdiciKusur = 0
        # örtü alanının bir el tespit edildiğinde bundan daha az bir area hull alanı olamayacağı tespit
        # edildi.Deneysel bir değerdir
        if area_hull > 6000:
            # kusurlarda gezildi,start,end ve örtüye en uzak nokta belirlendi
            for i in range(defects.shape[0]):
                s, e, f, d = defects[i, 0]
                start = tuple(approx[s][0])
                end = tuple(approx[e][0])
                far = tuple(approx[f][0])
                # bulunan kusurdaki açı değerinin bulunması için(bunun nedeni çok büyük
                # değerli açıların aslında iki parmağımın arasını göstermeyecek olduğu) start
                # end ve far noktaları arasındaki uzaklıklar buludu
                a = (((start[0] - end[0]) ** 2) + (start[1] - end[1]) ** 2) ** (1 / 2)
                b = (((start[0] - far[0]) ** 2) + (start[1] - far[1]) ** 2) ** (1 / 2)
                c = (((far[0] - end[0]) ** 2) + (far[1] - end[1]) ** 2) ** (1 / 2)
                # ALAN FORMULU
                ortalamaUzunluk = (a + b + c) / 2
                s = math.sqrt(ortalamaUzunluk * (ortalamaUzunluk - a) * (ortalamaUzunluk - b) * (ortalamaUzunluk - c))
                # örtü ile far noktası arasındaki uzaklığın bulunması
                d = (2 * s) / a
                # acinin aci değişkenine atanması
                aci = math.acos((b ** 2 + c ** 2 - a ** 2) / (2 * b * c)) * 57
                # acinin 90dan kucuk ve far noktası ile örtü arasındaki uzaklıgın 20 den uzun olması durumunda bu if
                # içine girilebiliyor
                if aci <= 90 and d > 20:
                    ayirtEdiciKusur += 1
                    # far noktalarına yuvarlak çizildi
                    cv2.circle(roi, far, 3, [255, 0, 0], -1)
                # kacparmakacmis değişkenine ayırt edici kusurun bir fazlası atandı(bir ve sıfırın kacparmakacmis
                # degeri 1 oldu bu durumda)
                kacParmakAcmis = ayirtEdiciKusur + 1
                # örtünün çizgileri çizildi
                cv2.line(roi, start, end, [0, 255, 0], 2)

        """
        
                                        DENEYSEL DEGERLER
                                        #KARAR VERME
            # 5 parmak acıkken       1 parmak açıkken       2 parmak açıkken    fist durumu
# area ratio    41.40                  29.175                   54.2275           15.45
#areahand=      16600                  10968                     10680             10175
#areahull=      23474                  14168                     16471             11747
        #el kamera acısına girdi
"""

        if area_hull > 6000:

            if kacParmakAcmis == 1:
                # yumruk
                if area_ratio < 17:
                    if eskiKacParmakAcmis == 5:
                        cv2.circle(frame, (450, 450), 25, (0, 255, 0), -1)
                        pyautogui.press("k")
                    eskiKacParmakAcmis = 0
                # bir parmak
                else:
                    # ilk girişte eskimerkezNoktasının atanması gerçekleştirildi
                    if eskiKacParmakAcmis != 1:
                        (merkezBirParmakx, merkezBirParmaky) = merkezNoktayiBul(contour)
                        eskiMerkezBirParmakx = merkezBirParmakx
                    else:
                        # eğer ilk giriş değilse, eski merkez baz alınarak eğer yeni merkez eski merkezin
                        # x degerinden2 fazla ise(deneysel deger) sağ,2 veya daha fazla az ise sol
                        (merkezBirParmakx, merkezBirParmaky) = merkezNoktayiBul(contour)
                        if merkezBirParmakx + 2 < eskiMerkezBirParmakx:
                            pyautogui.press("j")
                        elif merkezBirParmakx > eskiMerkezBirParmakx + 2:
                            pyautogui.press("l")
                        eskiMerkezBirParmakx = merkezBirParmakx
                    eskiKacParmakAcmis = 1
                # iki parmak
            if kacParmakAcmis == 2:
                # ilk girişte eskimerkezNoktasının atanması gerçekleştirildi
                if eskiKacParmakAcmis != 2:
                    (merkezIkiParmakx, merkezIkiParmaky) = merkezNoktayiBul(contour)
                    eskiMerkezIkiParmaky = merkezIkiParmaky
                else:
                    # eğer ilk giriş değilse, eski merkez baz alınarak eğer
                    # yeni merkez eski merkezin y degerinden
                    # 2 fazla ise(deneysel deger) up,2 veya daha az ise down
                    (merkezIkiParmakx, merkezIkiParmaky) = merkezNoktayiBul(contour)
                    if merkezIkiParmaky > eskiMerkezIkiParmaky + 2:
                        pyautogui.press("volumedown")
                    if merkezIkiParmaky + 2 < eskiMerkezIkiParmaky:
                        pyautogui.press("volumeup")
                    eskiMerkezIkiParmaky = merkezIkiParmaky
                eskiKacParmakAcmis = 2
            if kacParmakAcmis == 3 :
                if(eskiKacParmakAcmis==3):
                    kackere3yapmis=kackere3yapmis+1
                if(kackere3yapmis==40):
                    pyautogui.press("m")
                    kackere3yapmis =0
                eskiKacParmakAcmis=3
            elif kacParmakAcmis == 5:
                eskiKacParmakAcmis = 5

        else:
            cv2.putText(frame, "elinizi kutunun icine denk getirin", (0, 50), font, 1, (255, 165, 0), 1, cv2.LINE_AA)
    except:
        pass
    # frame imshow ile gösterildi
    cv2.imshow("alinan goruntu", frame)
    cv2.imshow("roi", mask_roi)
    # q tuşuna basıldığında çıkış sağlandı
    if cv2.waitKey(1) and 0xFF == ord("q"):
        break
# cap değişkenimiz serbest bırakıldı
cap.release()
# butun pencerelerin kapatıması sağlandı
cv2.destroyAllWindows()
