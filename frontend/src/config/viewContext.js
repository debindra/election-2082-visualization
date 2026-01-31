/**
 * View context for Storytelling with Data: audience, message, action, headline, takeaway per view.
 * Used for header/subtitle, focus lines, and "So what?" per tab. Supports language 'en' | 'ne'.
 */
export const VIEW_CONTEXT = {
  areas: {
    en: {
      audience: 'Journalists, researchers, citizens',
      message: 'Candidate counts and independents by region; drill from province to district to constituency.',
      action: 'Click a region to see candidates; use the breadcrumb to move between province, district, and constituency.',
      headline: 'Election areas',
      focusLine: 'Candidates and independents by region',
      takeaway: 'Click a region to see candidates; use the breadcrumb to move between province, district, and constituency.',
    },
    ne: {
      audience: 'पत्रकार, अनुसन्धानकर्ता, नागरिक',
      message: 'क्षेत्र अनुसार उम्मेदवार संख्या र स्वतन्त्र; प्रदेशबाट जिल्ला र निर्वाचन क्षेत्रसम्म ड्रिल गर्नुहोस्।',
      action: 'उम्मेदवार हेर्न क्षेत्र क्लिक गर्नुहोस्; प्रदेश, जिल्ला र निर्वाचन क्षेत्र बीच ब्रेडक्रम्ब प्रयोग गर्नुहोस्।',
      headline: 'निर्वाचन क्षेत्र',
      focusLine: 'क्षेत्र अनुसार उम्मेदवार र स्वतन्त्र',
      takeaway: 'उम्मेदवार हेर्न क्षेत्र क्लिक गर्नुहोस्; प्रदेश, जिल्ला र निर्वाचन क्षेत्र बीच ब्रेडक्रम्ब प्रयोग गर्नुहोस्।',
    },
  },
  insights: {
    en: {
      audience: 'Journalists, researchers, policymakers',
      message: 'Independent strength and competition intensity by district; year-level demographics and composite metrics.',
      action: 'Compare representation and competition across years; use filters to narrow by province or district.',
      headline: 'Insights',
      focusLine: 'Independent strength and competition intensity by district',
      takeaway: 'Use these metrics to compare representation and competition across years.',
    },
    ne: {
      audience: 'पत्रकार, अनुसन्धानकर्ता, नीति निर्माता',
      message: 'जिल्ला अनुसार स्वतन्त्र शक्ति र प्रतिस्पर्धा तीव्रता; वर्ष-स्तर जनसांख्यिकी र समग्र मेट्रिक्स।',
      action: 'वर्षहरूमा प्रतिनिधित्व र प्रतिस्पर्धा तुलना गर्नुहोस्; प्रदेश वा जिल्ला अनुसार फिल्टर प्रयोग गर्नुहोस्।',
      headline: 'अन्तर्दृष्टि',
      focusLine: 'जिल्ला अनुसार स्वतन्त्र शक्ति र प्रतिस्पर्धा तीव्रता',
      takeaway: 'वर्षहरूमा प्रतिनिधित्व र प्रतिस्पर्धा तुलना गर्न यी मेट्रिक्स प्रयोग गर्नुहोस्।',
    },
  },
  compare: {
    en: {
      audience: 'Researchers, journalists, citizens',
      message: 'Side-by-side comparison of up to 10 candidates by ID.',
      action: 'Enter candidate IDs to compare profiles, parties, and metrics.',
      headline: 'Compare candidates',
      focusLine: 'Compare candidates by ID',
      takeaway: 'Use these details to compare candidate profiles and party mix.',
    },
    ne: {
      audience: 'अनुसन्धानकर्ता, पत्रकार, नागरिक',
      message: 'आईडी अनुसार १० जना उम्मेदवारको पक्ष-by-पक्ष तुलना।',
      action: 'प्रोफाइल, दल र मेट्रिक्स तुलना गर्न उम्मेदवार आईडी प्रविष्ट गर्नुहोस्।',
      headline: 'उम्मेदवार तुलना',
      focusLine: 'आईडी अनुसार उम्मेदवार तुलना गर्नुहोस्',
      takeaway: 'उम्मेदवार प्रोफाइल र दल मिक्स तुलना गर्न यी विवरणहरू प्रयोग गर्नुहोस्।',
    },
  },
  trends: {
    en: {
      audience: 'Researchers, policymakers',
      message: 'Multi-year trends: independent shift, party footprint, age, education, and other analytics.',
      action: 'Select years to compare trends across election cycles.',
      headline: 'Trends',
      focusLine: 'Trends across election years',
      takeaway: 'Use these trends to see how the political landscape has changed over time.',
    },
    ne: {
      audience: 'अनुसन्धानकर्ता, नीति निर्माता',
      message: 'बहु-वर्ष प्रवृत्तिहरू: स्वतन्त्र परिवर्तन, दल पदचाप, उमेर, शिक्षा र अन्य विश्लेषण।',
      action: 'निर्वाचन चक्रहरूमा प्रवृत्ति तुलना गर्न वर्षहरू छान्नुहोस्।',
      headline: 'प्रवृत्तिहरू',
      focusLine: 'निर्वाचन वर्षहरूमा प्रवृत्तिहरू',
      takeaway: 'समयको साथ राजनीतिक परिदृश्य कसरी बदलिएको हेर्न यी प्रवृत्तिहरू प्रयोग गर्नुहोस्।',
    },
  },
};

/**
 * Get view context for a tab and language.
 * @param {string} viewKey - 'areas' | 'insights' | 'compare' | 'trends'
 * @param {string} language - 'en' | 'ne'
 */
export function getViewContext(viewKey, language = 'en') {
  const view = VIEW_CONTEXT[viewKey];
  if (!view) return null;
  return view[language === 'ne' ? 'ne' : 'en'] || view.en;
}
