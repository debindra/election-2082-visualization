/**
 * Legal and policy content (Disclaimer, Privacy, Terms, Data sources).
 * Bilingual (en / ne). Election data attributed to https://election.gov.np/
 */

const ELECTION_GOV_NP = 'https://election.gov.np/';
const GEOJSON_SOURCE = 'https://github.com/mesaugat/geoJSON-Nepal';

export const LEGAL_PAGES = {
  disclaimer: {
    en: {
      title: 'Disclaimer',
      content: `
## Data & policy disclaimer

This visualization is **for informational and research purposes only**. It is not an official product of the Election Commission of Nepal (ECN).

- **Election data**: Candidate and election data used in this system are derived from information published or made available by the [Election Commission, Nepal](${ELECTION_GOV_NP}). Data may have been processed, aggregated, or combined with other sources for visualization.
- **Accuracy**: We do not guarantee the accuracy, completeness, or timeliness of the data. Where vote-level data is missing, some metrics use fallbacks (e.g. candidate-based share instead of vote share); see **Data sources** for methodology.
- **Not legal advice**: This tool does not constitute legal, electoral, or official advice. For official results and voter services, use the [Election Commission, Nepal](${ELECTION_GOV_NP}) website.
- **Use at your own risk**: Use of this system is at your own risk. The operators are not liable for any decisions made based on this visualization.
      `.trim(),
    },
    ne: {
      title: 'अस्वीकरण',
      content: `
## डाटा र नीति अस्वीकरण

यो दृश्यीकरण **सूचनात्मक र अनुसन्धान उद्देश्यको लागि मात्र** हो। यो नेपाल निर्वाचन आयोग (ECN) को आधिकारिक उत्पादन होइन।

- **निर्वाचन डाटा**: यो प्रणालीमा प्रयोग गरिएको उम्मेदवार र निर्वाचन डाटा [नेपाल निर्वाचन आयोग](${ELECTION_GOV_NP}) ले प्रकाशन वा उपलब्ध गराएको जानकारीबाट लिइएको हो। डाटा दृश्यीकरणको लागि प्रशोधन, समग्र वा अन्य स्रोतहरूसँग मिलाइएको हुन सक्छ।
- **सटीकता**: हामी डाटाको सटीकता, पूर्णता वा समयमैता ग्यारेन्टी दिन्दैनौं। जहाँ मत-स्तर डाटा हराएको छ, केही मेट्रिक्सले फलब्याक प्रयोग गर्दछ (जस्तै मत शेयरको सट्टा उम्मेदवार-आधारित शेयर); विधि को लागि **डाटा स्रोत** हेर्नुहोस्।
- **कानूनी सल्लाह होइन**: यो उपकरण कानूनी, निर्वाचन, वा आधिकारिक सल्लाह होइन। आधिकारिक नतिजा र मतदाता सेवाको लागि [नेपाल निर्वाचन आयोग](${ELECTION_GOV_NP}) वेबसाइट प्रयोग गर्नुहोस्।
- **आफ्नो जोखिममा प्रयोग गर्नुहोस्**: यो प्रणालीको प्रयोग आफ्नो जोखिममा हो। यो दृश्यीकरणको आधारमा गरिएका कुनै पनि निर्णयको लागि सञ्चालक जिम्मेवार छैनन्।
      `.trim(),
    },
  },
  privacy: {
    en: {
      title: 'Privacy',
      content: `
## Privacy

- **Local storage**: This app may store your **language preference** (English / नेपाली) in your browser’s local storage so your choice is remembered on the next visit. No personal data is sent to any server for this.
- **Election data**: The election data shown (candidates, parties, districts, etc.) comes from [Election Commission, Nepal](${ELECTION_GOV_NP}) and is processed for visualization. We do not collect or store your personal information through this app.
- **Third parties**: Map tiles may be loaded from third-party servers (e.g. OpenStreetMap). Their privacy policies apply to those requests. We do not pass your identity to them.
- **Changes**: We may update this privacy notice; the current version applies when you use the app.
      `.trim(),
    },
    ne: {
      title: 'गोपनीयता',
      content: `
## गोपनीयता

- **लोकल स्टोरेज**: यो ऐपले तपाईंको **भाषा प्राथमिकता** (अङ्ग्रेजी / नेपाली) ब्राउजरको लोकल स्टोरेजमा सङ्ग्रह गर्न सक्छ ताकि अर्को पटक भ्रमणमा तपाईंको छनौट सम्झन सकियोस्। यसको लागि कुनै व्यक्तिगत डाटा कुनै सर्भरमा पठाइँदैन।
- **निर्वाचन डाटा**: देखाइएको निर्वाचन डाटा (उम्मेदवार, दल, जिल्ला आदि) [नेपाल निर्वाचन आयोग](${ELECTION_GOV_NP}) बाट आउँछ र दृश्यीकरणको लागि प्रशोधन गरिएको छ। हामी यो ऐप मार्फत तपाईंको व्यक्तिगत जानकारी सङ्ग्रह वा भण्डारण गर्दैनौं।
- **तृतीय पक्ष**: नक्शा टाइलहरू तृतीय-पक्ष सर्भरहरूबाट लोड हुन सक्छन् (जस्तै OpenStreetMap)। उनीहरूको गोपनीयता नीति ती अनुरोधहरूमा लागू हुन्छ। हामी तपाईंको पहिचान उनीहरूलाई पठाउँदैनौं।
- **परिवर्तन**: हामी यो गोपनीयता सूचना अपडेट गर्न सक्छौं; ऐप प्रयोग गर्दा हालको संस्करण लागू हुन्छ।
      `.trim(),
    },
  },
  terms: {
    en: {
      title: 'Terms of use',
      content: `
## Terms of use

By using this Nepal House of Representatives Election Data Visualization system, you agree to the following:

- **Informational use**: The system is provided for education, research, and general information only. Do not rely on it for official electoral or legal decisions.
- **Acceptable use**: Do not use the system to harass, misrepresent, or violate any applicable laws. Do not attempt to overload or disrupt the service.
- **No warranty**: The system is provided "as is" without warranties of any kind. We are not liable for any loss or damage arising from your use of the system.
- **Data**: Election data is sourced from [Election Commission, Nepal](${ELECTION_GOV_NP}) and other documented sources. You are responsible for how you use or cite this data.
- **Changes**: We may change these terms; continued use of the app after changes constitutes acceptance.
      `.trim(),
    },
    ne: {
      title: 'प्रयोगका सर्तहरू',
      content: `
## प्रयोगका सर्तहरू

यो नेपाल प्रतिनिधिसभा निर्वाचन डाटा दृश्यीकरण प्रणाली प्रयोग गरेर, तपाईं निम्न स्वीकार गर्नुहुन्छ:

- **सूचनात्मक प्रयोग**: प्रणाली शिक्षा, अनुसन्धान र सामान्य जानकारीको लागि मात्र प्रदान गरिएको हो। आधिकारिक निर्वाचन वा कानूनी निर्णयको लागि यसमा भर पर्नुहुन्न।
- **स्वीकार्य प्रयोग**: प्रणाली उत्पीडन, गलत प्रस्तुतीकरण वा लागू कानून उल्लंघन गर्न प्रयोग नगर्नुहोस्। सेवा अधिभार वा बिच्छेदन गर्न प्रयास नगर्नुहोस्।
- **कुनै वारेन्टी छैन**: प्रणाली "जस्तै छ" कुनै पनि प्रकारको वारेन्टी बिना प्रदान गरिएको हो। प्रणाली प्रयोगबाट हुने कुनै पनि हानि वा क्षतिको लागि हामी जिम्मेवार छैनौं।
- **डाटा**: निर्वाचन डाटा [नेपाल निर्वाचन आयोग](${ELECTION_GOV_NP}) र अन्य दस्तावेजीकृत स्रोतहरूबाट लिइएको हो। तपाईं यो डाटा कसरी प्रयोग वा उद्धरण गर्नुहुन्छ भन्नेको लागि जिम्मेवार हुनुहुन्छ।
- **परिवर्तन**: हामी यी सर्तहरू परिवर्तन गर्न सक्छौं; परिवर्तन पछि ऐपको निरन्तर प्रयोगले स्वीकृतिलाई निर्माण गर्दछ।
      `.trim(),
    },
  },
  dataSources: {
    en: {
      title: 'Data sources',
      content: `
## Data sources & attribution

- **Election data**: Candidate and election statistics (names, parties, districts, constituencies, votes, etc.) are derived from data published or made available by the [Election Commission, Nepal](${ELECTION_GOV_NP}). Data may have been crawled, cleaned, and aggregated for this visualization. This is not an official ECN product.
- **Map boundaries**: District-level boundaries use GeoJSON from [geoJSON-Nepal](${GEOJSON_SOURCE}) (nepal-districts.geojson). Province and constituency geometries may use placeholder or synthetic polygons where official GeoJSON is not available. See the project’s \`data/geojson/README.md\` for details.
- **Map tiles**: The interactive map uses MapLibre GL with tile data from OpenStreetMap contributors. Map attribution is shown on the map.
- **Exact vs estimated metrics**: Where vote data is missing, some insights use fallbacks (e.g. candidate-based share instead of vote share). The API and UI indicate the method used (e.g. "vote share" vs "candidate share"). See the project’s **Data Governance** documentation for full methodology.
      `.trim(),
    },
    ne: {
      title: 'डाटा स्रोत',
      content: `
## डाटा स्रोत र उल्लेख

- **निर्वाचन डाटा**: उम्मेदवार र निर्वाचन तथ्याङ्क (नाम, दल, जिल्ला, निर्वाचन क्षेत्र, मत आदि) [नेपाल निर्वाचन आयोग](${ELECTION_GOV_NP}) ले प्रकाशन वा उपलब्ध गराएको डाटाबाट लिइएको हो। यो दृश्यीकरणको लागि डाटा क्रल, सफा र समग्र गरिएको हुन सक्छ। यो आधिकारिक ECN उत्पादन होइन।
- **नक्शा सीमाहरू**: जिल्ला-स्तर सीमाहरू [geoJSON-Nepal](${GEOJSON_SOURCE}) (nepal-districts.geojson) बाट GeoJSON प्रयोग गर्दछ। प्रदेश र निर्वाचन क्षेत्र ज्यामितिहरूले आधिकारिक GeoJSON उपलब्ध नभएको ठाउँमा प्लेसहोल्डर वा कृत्रिम बहुभुज प्रयोग गर्न सक्छ। विवरणको लागि परियोजनाको \`data/geojson/README.md\` हेर्नुहोस्।
- **नक्शा टाइलहरू**: इन्टरएक्टिभ नक्शाले OpenStreetMap योगदानकर्ताहरूबाट टाइल डाटा सहित MapLibre GL प्रयोग गर्दछ। नक्शामा नक्शा उल्लेख देखाइन्छ।
- **सटीक बनाम अनुमानित मेट्रिक्स**: जहाँ मत डाटा हराएको छ, केही अन्तर्दृष्टिहरूले फलब्याक प्रयोग गर्दछ (जस्तै मत शेयरको सट्टा उम्मेदवार-आधारित शेयर)। API र UI ले प्रयोग गरिएको विधि संकेत गर्दछ (जस्तै "मत शेयर" बनाम "उम्मेदवार शेयर")। पूर्ण विधि को लागि परियोजनाको **डाटा शासन** कागजात हेर्नुहोस्।
      `.trim(),
    },
  },
};

/**
 * Get legal page content for a page key and language.
 * @param {string} pageKey - 'disclaimer' | 'privacy' | 'terms' | 'dataSources'
 * @param {string} language - 'en' | 'ne'
 */
export function getLegalContent(pageKey, language = 'en') {
  const page = LEGAL_PAGES[pageKey];
  if (!page) return null;
  const lang = language === 'ne' ? 'ne' : 'en';
  return page[lang] || page.en;
}
