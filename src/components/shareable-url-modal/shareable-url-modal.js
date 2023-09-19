import React, { useEffect, useState } from 'react';
import { connect } from 'react-redux';
import classnames from 'classnames';
import { toggleShareableUrlModal } from '../../actions';
import modifiers from '../../utils/modifiers';
import { isRunningLocally } from '../../utils';

import Button from '../ui/button';
import CopyIcon from '../icons/copy';
import Dropdown from '../ui/dropdown';
import IconButton from '../ui/icon-button';
import Input from '../ui/input';
import LoadingIcon from '../icons/loading';
import Modal from '../ui/modal';
import MenuOption from '../ui/menu-option';

import './shareable-url-modal.scss';

const s3BucketRegions = [
  'us-east-2',
  'us-east-1',
  'us-west-1',
  'us-west-2',
  'af-south-1',
  'ap-east-1',
  'ap-south-2',
  'ap-southeast-3',
  'ap-southeast-4',
  'ap-south-1',
  'ap-northeast-3',
  'ap-northeast-2',
  'ap-southeast-1',
  'ap-southeast-2',
  'ap-northeast-1',
  'ca-central-1',
  'cn-north-1',
  'cn-northwest-1',
  'eu-central-1',
  'eu-west-1',
  'eu-west-2',
  'eu-south-1',
  'eu-west-3',
  'eu-north-1',
  'eu-south-2',
  'eu-central-2',
  'sa-east-1',
  'me-south-1',
  'me-central-1',
  'il-central-1',
];

const modalMessages = (status, info = '') => {
  const messages = {
    default:
      'Please enter your AWS information and a hosted link will be generated.',
    failure: 'Something went wrong. Please try again later.',
    loading: 'Shooting your files through space. Sit tight...',
    success:
      'The current version of Kedro-Viz has been deployed and hosted via the link below.',
    incompatible: `Deploying and hosting Kedro-Viz is only supported with fsspec >=2023.9.0. You are currently on version ${info}.\n\nPlease upgrade fsspec to a supported version and ensure you're using Kedro 0.18.2 or above.`,
  };

  return messages[status];
};

const ShareableUrlModal = ({ onToggle, visible }) => {
  const [deploymentState, setDeploymentState] = useState('default');
  const [inputValues, setInputValues] = useState({});
  console.log('inputValues: ', inputValues);
  const [hasNotInteracted, setHasNotInteracted] = useState(true);
  const [isLoading, setIsLoading] = useState(false);
  const [responseUrl, setResponseUrl] = useState(null);
  const [showCopied, setShowCopied] = useState(false);
  const [isLinkSettingsClick, setIsLinkSettingsClick] = useState(false);
  const [compatibilityData, setCompatibilityData] = useState({});
  const [canUseShareableUrls, setCanUseShareableUrls] = useState(true);

  useEffect(() => {
    try {
      async function fetchPackageCompatibility() {
        const request = await fetch('/api/package_compatibilities', {
          headers: {
            'Content-Type': 'application/json',
            Accept: 'application/json',
          },
        });
        const response = await request.json();

        if (request.ok) {
          setCompatibilityData(response);
          setCanUseShareableUrls(response?.is_compatible || false);

          // User's fsspec package version isn't compatible, so set
          // the necessary state to reflect that in the UI.
          if (!response.is_compatible) {
            setDeploymentState(!response.is_compatible && 'incompatible');
          }
        }
      }

      if (isRunningLocally()) {
        fetchPackageCompatibility();
      }
    } catch (error) {
      console.log('package_compatibilities fetch error: ', error);
    }
  }, []);

  const onChange = (key, value) => {
    setHasNotInteracted(false);
    setInputValues(
      Object.assign({}, inputValues, {
        [key]: value,
      })
    );
  };

  const handleSubmit = async () => {
    setDeploymentState('loading');
    setIsLoading(true);

    try {
      const request = await fetch('/api/deploy', {
        headers: {
          'Content-Type': 'application/json',
        },
        method: 'POST',
        body: JSON.stringify(inputValues),
      });
      const response = await request.json();

      if (request.ok) {
        setResponseUrl(response.url);
        setDeploymentState('success');
      } else {
        setResponseUrl('Something went wrong.');
        setDeploymentState('failure');
      }
    } catch (error) {
      console.error(error);
      setDeploymentState('failure');
    } finally {
      setIsLoading(false);
    }
  };

  const onCopyClick = () => {
    window.navigator.clipboard.writeText(responseUrl);
    setShowCopied(true);
    setTimeout(() => setShowCopied(false), 1500);
  };

  const handleModalClose = () => {
    onToggle(false);
    setDeploymentState('default');
    setIsLoading(false);
    setResponseUrl(null);
    setIsLinkSettingsClick(false);
    setInputValues({});
  };

  return (
    <Modal
      className="shareable-url-modal"
      closeModal={() => onToggle(false)}
      message={modalMessages(
        deploymentState,
        compatibilityData.package_version
      )}
      title={
        deploymentState === 'success'
          ? 'Kedro-Viz Hosted and Deployed'
          : 'Deploy and Share Kedro-Viz'
      }
      visible={visible.shareableUrlModal}
    >
      {!isLoading && !responseUrl && canUseShareableUrls ? (
        <>
          <div className="shareable-url-modal__input-wrapper">
            <div className="shareable-url-modal__input-label">
              AWS Bucket Region
            </div>
            <Dropdown
              defaultText={inputValues?.region || 'Choose a region...'}
              onChanged={(selectedRegion) => {
                onChange('region', selectedRegion.value);
              }}
              width={null}
            >
              {s3BucketRegions.map((region) => {
                return (
                  <MenuOption
                    className={classnames({
                      'pipeline-list__option--active':
                        inputValues.region === region,
                    })}
                    key={region}
                    primaryText={region}
                    value={region}
                  />
                );
              })}
            </Dropdown>
          </div>
          <div className="shareable-url-modal__input-wrapper">
            <div className="shareable-url-modal__input-label">Bucket Name</div>
            <Input
              defaultValue={inputValues.bucket_name}
              onChange={(value) => onChange('bucket_name', value)}
              placeholder="s3://my-bucket-name"
              resetValueTrigger={visible}
              size="large"
            />
          </div>
          <div className="shareable-url-modal__button-wrapper shareable-url-modal__button-wrapper--right">
            <Button
              mode="secondary"
              onClick={() => handleModalClose()}
              size="small"
            >
              Cancel
            </Button>
            <Button
              disabled={hasNotInteracted}
              size="small"
              onClick={handleSubmit}
            >
              {isLinkSettingsClick ? 'Re-Deploy' : 'Deploy'}
            </Button>
          </div>
        </>
      ) : null}
      {isLoading ? (
        <div className="shareable-url-modal__loading">
          <LoadingIcon visible={isLoading} />
        </div>
      ) : null}
      {responseUrl ? (
        <>
          <div className="shareable-url-modal__result">
            <div className="shareable-url-modal__label">Hosted link</div>
            <div className="shareable-url-modal__url-wrapper">
              <a
                className={modifiers('shareable-url-modal__result-url', {
                  visible: !showCopied,
                })}
                href={responseUrl}
                target="_blank"
                rel="noopener noreferrer"
              >
                {responseUrl}
              </a>
              {window.navigator.clipboard && (
                <>
                  <span
                    className={modifiers('copy-message', {
                      visible: showCopied,
                    })}
                  >
                    Copied to clipboard.
                  </span>
                  <IconButton
                    ariaLabel="Copy run command to clipboard."
                    className="copy-button"
                    dataHeapEvent={`clicked.run_command`}
                    icon={CopyIcon}
                    onClick={onCopyClick}
                  />
                </>
              )}
            </div>
          </div>
          <div className="shareable-url-modal__button-wrapper ">
            <Button
              mode="secondary"
              onClick={() => {
                setDeploymentState('default');
                setIsLoading(false);
                setResponseUrl(null);
                setIsLinkSettingsClick(true);
              }}
              size="small"
            >
              Link Settings
            </Button>
            <Button
              mode="secondary"
              onClick={() => handleModalClose()}
              size="small"
            >
              Close
            </Button>
          </div>
        </>
      ) : null}
    </Modal>
  );
};

export const mapStateToProps = (state) => ({
  visible: state.visible,
});

export const mapDispatchToProps = (dispatch) => ({
  onToggle: (value) => {
    dispatch(toggleShareableUrlModal(value));
  },
});

export default connect(mapStateToProps, mapDispatchToProps)(ShareableUrlModal);
